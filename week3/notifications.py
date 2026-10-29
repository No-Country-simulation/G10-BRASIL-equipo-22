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
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("mediflow.notifications")


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
    ) -> None:
        self.webhook_url = webhook_url or os.getenv("WEBHOOK_EMERGENCY_URL", "")
        self.timeout = timeout_seconds
        self.mock_mode = mock_mode or not bool(self.webhook_url)
        self.historico_alertas: List[AlertaClinicoRegistro] = []

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
            logger.info("Mock Webhook disparado com sucesso para %s (Doc: %s)", canal, documento_id)
            registro = AlertaClinicoRegistro(
                documento_id=documento_id,
                paciente_nome=paciente,
                diagnostico=diag,
                crm_solicitante=crm,
                prioridade="Urgente",
                canal=canal,
                mensagem=mensagem,
                status_entrega="sucesso_mock",
                resposta_servidor="200 OK (Simulado)",
                latencia_ms=12.5,
            )
            self.historico_alertas.append(registro)
            return {
                "status_envio": "sucesso_mock",
                "canal": canal,
                "mensagem": mensagem,
                "payload": payload,
            }

        # Envio HTTP real para Webhook externo
        t_inicio = datetime.datetime.now()
        try:
            headers = {"Content-Type": "application/json", "User-Agent": "MediFlow-Agent/1.3"}
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.webhook_url, json=payload, headers=headers)
                latencia = (datetime.datetime.now() - t_inicio).total_seconds() * 1000

                status_envio = "sucesso" if resp.is_success else f"erro_http_{resp.status_code}"
                registro = AlertaClinicoRegistro(
                    documento_id=documento_id,
                    paciente_nome=paciente,
                    diagnostico=diag,
                    crm_solicitante=crm,
                    prioridade="Urgente",
                    canal=canal,
                    mensagem=mensagem,
                    status_entrega=status_envio,
                    resposta_servidor=resp.text[:200],
                    latencia_ms=round(latencia, 2),
                )
                self.historico_alertas.append(registro)
                return {
                    "status_envio": status_envio,
                    "canal": canal,
                    "mensagem": mensagem,
                    "latencia_ms": round(latencia, 2),
                }

        except Exception as exc:
            latencia = (datetime.datetime.now() - t_inicio).total_seconds() * 1000
            logger.warning("Falha no disparo do Webhook externo (%s). Registrando fallback local.", exc)
            registro = AlertaClinicoRegistro(
                documento_id=documento_id,
                paciente_nome=paciente,
                diagnostico=diag,
                crm_solicitante=crm,
                prioridade="Urgente",
                canal=canal,
                mensagem=mensagem,
                status_entrega="falha_conexao_fallback_local",
                resposta_servidor=str(exc),
                latencia_ms=round(latencia, 2),
            )
            self.historico_alertas.append(registro)
            return {
                "status_envio": "falha_conexao_fallback_local",
                "canal": canal,
                "mensagem": mensagem,
                "detalhes": str(exc),
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
                "status": r.status_entrega,
                "latencia_ms": r.latencia_ms,
                "timestamp": r.timestamp,
            }
            for r in self.historico_alertas[-limit:]
        ]

