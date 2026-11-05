"""
MediFlow — Módulo de Workflows de Notificação & Webhooks em Tempo Real (Release 1.3)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Persona Responsável: Fernando Nexus (Fernando Szekut — Engenheiro de Integração de Agentes & Workflows)
Supervisão de Arquitetura SRE: Carlos Magno (Tech Lead & SRE/DevOps)
"""

from __future__ import annotations

import datetime
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger("mediflow.notifications")

# Erros em que vale tentar de novo; 4xx de URL ou token errado não melhora com nova tentativa
STATUS_HTTP_TRANSITORIOS = {408, 425, 429, 500, 502, 503, 504}


@dataclass
class AlertaClinicoRegistro:
    """Registro estruturado de notificação disparada pelo agente."""

    documento_id: str
    paciente_nome: str
    diagnostico: str
    crm_solicitante: str
    prioridade: str
    canal: str
    mensagem: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    status_entrega: str = "enviado"
    resposta_servidor: Optional[str] = None
    latencia_ms: float = 0.0
    tentativas: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)
    # Identifica o alerta na aba de histórico e no reenvio manual (CARD-18)
    alerta_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    reenvios: int = 0
    ultimo_reenvio: Optional[str] = None

    @property
    def entregue(self) -> bool:
        """Só o webhook real confirmado conta; o modo simulado não avisou ninguém."""
        return self.status_entrega == "sucesso"


class NotificationDispatcher:
    """
    Despachador de notificações e Webhooks para equipes médicas em tempo real.
    Garante que achados críticos de urgência (como TEP Agudo e IAM) alcancem
    instantaneamente os canais hospitalares (Slack, Discord, Pager ou Webhook REST).
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        timeout_seconds: float = 3.0,
        mock_mode: bool = False,
        max_tentativas: int = 2,
        espera_entre_tentativas: float = 0.5,
    ) -> None:
        self.webhook_url = webhook_url or os.getenv("WEBHOOK_EMERGENCY_URL", "")
        self.timeout = timeout_seconds
        self.mock_mode = mock_mode or not bool(self.webhook_url)
        self.max_tentativas = max(1, max_tentativas)
        self.espera_entre_tentativas = espera_entre_tentativas
        self.historico_alertas: List[AlertaClinicoRegistro] = []

        # Sem URL o alerta não sai do MediFlow: avisar alto em vez de fingir entrega
        if self.mock_mode and not mock_mode:
            logger.warning(
                "WEBHOOK_EMERGENCY_URL não configurada: alertas de plantão ficam só no histórico local (modo simulado)."
            )

    def dispatch_emergency_alert(
        self,
        documento_id: str,
        paciente_nome: Optional[str],
        diagnostico: Optional[str],
        crm_solicitante: Optional[str],
        canal: str = "Alerta_Plantao_Medico",
        mensagem_customizada: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dispara um alerta crítico de urgência médica para a equipe de plantão.
        """
        paciente = paciente_nome or "Paciente Não Identificado"
        diag = diagnostico or "Condição Crítica Aguda"
        crm = crm_solicitante or "CRM Não Especificado"

        mensagem = mensagem_customizada or (
            f"🚨 ALERTA CRÍTICO DE PLANTÃO MÉDICO | Doc: {documento_id}\n"
            f"Paciente: {paciente} | Diagnóstico: {diag}\n"
            f"Médico Solicitante: {crm} | Encaminhado imediatamente para Fila_Emergencia_Medica."
        )

        payload = {
            "evento": "ALERTA_EMERGENCIA_MEDICA",
            "documento_id": documento_id,
            "prioridade": "Urgente",
            "paciente": paciente,
            "diagnostico": diag,
            "crm_medico": crm,
            "canal_destino": canal,
            "mensagem": mensagem,
            "timestamp": datetime.datetime.now().isoformat(),
            "origem": "MediFlow Agent LangGraph StateGraph (Release 1.3)",
        }

        # Modo Mock (Zero Downtime / Demonstração local sem URL externa)
        if self.mock_mode:
            logger.info("Mock Webhook registrado para %s (Doc: %s); nada foi enviado", canal, documento_id)
            self._registrar(
                documento_id, paciente, diag, crm, canal, mensagem, payload,
                status_entrega="sucesso_mock",
                resposta_servidor="simulado: nenhum webhook configurado" if not self.webhook_url else "simulado (mock_mode)",
                latencia_ms=0.0,
                tentativas=0,
            )
            return {
                "status_envio": "sucesso_mock",
                "canal": canal,
                "mensagem": mensagem,
                "payload": payload,
            }

        # Envio HTTP real para Webhook externo
        status_envio, resposta, latencia, tentativas = self._enviar(payload)
        self._registrar(
            documento_id, paciente, diag, crm, canal, mensagem, payload,
            status_entrega=status_envio,
            resposta_servidor=resposta,
            latencia_ms=latencia,
            tentativas=tentativas,
        )
        resultado = {
            "status_envio": status_envio,
            "canal": canal,
            "mensagem": mensagem,
            "latencia_ms": latencia,
            "tentativas": tentativas,
        }
        if status_envio != "sucesso":
            # Emergência sem entrega confirmada: o histórico marca para reenvio e o log grita
            logger.error(
                "Alerta de plantão NÃO entregue (Doc: %s, %s após %d tentativa(s)): %s",
                documento_id, status_envio, tentativas, resposta,
            )
            resultado["detalhes"] = resposta
        return resultado

    def _enviar(self, payload: Dict[str, Any]) -> Tuple[str, Optional[str], float, int]:
        """POST com nova tentativa em erro transitório. Devolve (status, resposta, latência ms, tentativas)."""
        headers = {"Content-Type": "application/json", "User-Agent": "MediFlow-Agent/1.3"}
        status_envio, resposta = "falha_conexao", None
        t_inicio = time.perf_counter()
        tentativa = 0
        for tentativa in range(1, self.max_tentativas + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(self.webhook_url, json=payload, headers=headers)
                    resposta = resp.text[:200]
                if resp.is_success:
                    status_envio = "sucesso"
                    break
                status_envio = f"erro_http_{resp.status_code}"
                if resp.status_code not in STATUS_HTTP_TRANSITORIOS:
                    break
            except Exception as exc:  # rede, timeout, URL inválida
                status_envio, resposta = "falha_conexao", str(exc)
            if tentativa < self.max_tentativas:
                time.sleep(self.espera_entre_tentativas * tentativa)
        latencia = round((time.perf_counter() - t_inicio) * 1000, 2)
        return status_envio, resposta, latencia, tentativa

    def _registrar(
        self,
        documento_id: str,
        paciente: str,
        diagnostico: str,
        crm: str,
        canal: str,
        mensagem: str,
        payload: Dict[str, Any],
        **entrega: Any,
    ) -> AlertaClinicoRegistro:
        registro = AlertaClinicoRegistro(
            documento_id=documento_id,
            paciente_nome=paciente,
            diagnostico=diagnostico,
            crm_solicitante=crm,
            prioridade="Urgente",
            canal=canal,
            mensagem=mensagem,
            payload=payload,
            **entrega,
        )
        self.historico_alertas.append(registro)
        return registro

    def pode_reenviar(self, registro: AlertaClinicoRegistro) -> bool:
        """Só alerta real que não chegou ao plantão; no modo simulado não há para onde reenviar."""
        return not registro.entregue and not self.mock_mode

    def reenviar(self, alerta_id: str) -> Dict[str, Any]:
        """
        Reenvio manual (CARD-18) de um alerta que não chegou ao plantão.

        Manda o payload original, marcado com reenvio_manual (1, 2, ...) para o receptor poder
        descartar duplicata, e atualiza o mesmo registro do histórico: status e resposta passam a
        ser os do reenvio, latencia_ms é a do reenvio e tentativas soma todas as feitas.
        """
        registro = next((r for r in self.historico_alertas if r.alerta_id == alerta_id), None)
        if registro is None:
            raise KeyError(f"Alerta {alerta_id} não está no histórico desta sessão.")
        if registro.entregue:
            return {"status_envio": "ja_entregue", "alerta_id": alerta_id}
        if self.mock_mode:
            return {"status_envio": "sem_webhook", "alerta_id": alerta_id}

        agora = datetime.datetime.now().isoformat()
        payload = {**registro.payload, "reenvio_manual": registro.reenvios + 1, "timestamp_reenvio": agora}
        status_envio, resposta, latencia, tentativas = self._enviar(payload)

        registro.status_entrega = status_envio
        registro.resposta_servidor = resposta
        registro.latencia_ms = latencia
        registro.tentativas += tentativas
        registro.reenvios += 1
        registro.ultimo_reenvio = agora

        if status_envio == "sucesso":
            logger.info("Alerta %s (Doc: %s) entregue no reenvio manual %d", alerta_id, registro.documento_id, registro.reenvios)
        else:
            logger.error(
                "Reenvio manual do alerta %s (Doc: %s) também falhou: %s, %s",
                alerta_id, registro.documento_id, status_envio, resposta,
            )
        return {
            "status_envio": status_envio,
            "alerta_id": alerta_id,
            "latencia_ms": latencia,
            "tentativas": tentativas,
            "reenvios": registro.reenvios,
            "detalhes": resposta,
        }

    def resumo_entregas(self) -> Dict[str, Any]:
        """Números para o topo da aba: quantos chegaram, quantos não, e a latência dos envios reais."""
        reais = [r for r in self.historico_alertas if r.status_entrega != "sucesso_mock"]
        latencias = [r.latencia_ms for r in reais if r.tentativas > 0]
        return {
            "total": len(self.historico_alertas),
            "entregues": sum(1 for r in self.historico_alertas if r.entregue),
            "nao_entregues": sum(1 for r in reais if not r.entregue),
            "simulados": len(self.historico_alertas) - len(reais),
            "latencia_media_ms": round(sum(latencias) / len(latencias), 2) if latencias else None,
            "latencia_max_ms": max(latencias) if latencias else None,
        }

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna os últimos alertas clínicos registrados para auditoria visual."""
        return [
            {
                "documento_id": r.documento_id,
                "paciente": r.paciente_nome,
                "diagnostico": r.diagnostico,
                "crm": r.crm_solicitante,
                "canal": r.canal,
                "mensagem": r.mensagem,
                "status": r.status_entrega,
                "entregue": r.entregue,
                "tentativas": r.tentativas,
                "resposta_servidor": r.resposta_servidor,
                "latencia_ms": r.latencia_ms,
                "timestamp": r.timestamp,
                "alerta_id": r.alerta_id,
                "reenvios": r.reenvios,
                "ultimo_reenvio": r.ultimo_reenvio,
                "pode_reenviar": self.pode_reenviar(r),
            }
            for r in self.historico_alertas[-limit:]
        ]
