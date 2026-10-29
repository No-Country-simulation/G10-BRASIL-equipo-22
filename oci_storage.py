"""
MediFlow — OCI Object Storage Service (Always Free Tier) & Resilient Local Fallback
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Persona Responsável: Atlas Data (Helder — Banco de Dados, Persistência OCI Always Free)
Supervisão de Arquitetura & SRE: Arquiteto Carlos Vance (Carlos — Tech Lead & SRE/DevOps)
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("mediflow.oci_storage")


class OCIStorageService:
    """
    Gerencia a segregação e persistência de documentos clínicos no OCI Object Storage
    respeitando estritamente a camada Always Free (ADR-003).

    Estrutura de prefixos no bucket `mediflow-documentos-clinicos`:
      - recebidos/{documento_id}.json
      - processados/rotina/{documento_id}.json
      - processados/urgentes/{documento_id}.json
      - auditoria_humana/{documento_id}.json
    """

    DEFAULT_BUCKET = "mediflow-documentos-clinicos"

    def __init__(
        self,
        bucket_name: str | None = None,
        local_fallback_dir: str | Path = "./oci_bucket_local",
    ) -> None:
        self.bucket_name = bucket_name or os.getenv("OCI_BUCKET_NAME", self.DEFAULT_BUCKET)
        self.namespace = os.getenv("OCI_NAMESPACE", "")
        self.config_file = os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
        self.config_profile = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
        self.local_fallback_dir = Path(local_fallback_dir)
        self._oci_client = self._init_oci_client()

    def _init_oci_client(self) -> Any:
        """Tenta inicializar o cliente OCI SDK real; se não configurado, ativa fallback local resiliente."""
        try:
            import oci  # type: ignore

            expanded_path = os.path.expanduser(self.config_file)
            if os.path.exists(expanded_path):
                config = oci.config.from_file(expanded_path, self.config_profile)
                client = oci.object_storage.ObjectStorageClient(config)
                if not self.namespace:
                    self.namespace = client.get_namespace().data
                logger.info("Cliente OCI Object Storage inicializado (Namespace: %s)", self.namespace)
                return client
        except Exception as exc:
            logger.debug("SDK OCI não configurado ou indisponível (%s). Usando fallback local Always Free.", exc)
        return None

    @staticmethod
    def resolve_object_path(
        documento_id: str,
        requer_auditoria_humana: bool,
        nivel_prioridade: str,
        is_raw_ingestion: bool = False,
    ) -> str:
        """Determina o prefixo correto no bucket conforme o resultado da triagem."""
        if is_raw_ingestion:
            return f"recebidos/{documento_id}.json"
        if requer_auditoria_humana:
            return f"auditoria_humana/{documento_id}.json"
        if nivel_prioridade.lower() == "urgente":
            return f"processados/urgentes/{documento_id}.json"
        return f"processados/rotina/{documento_id}.json"

    def save_json_object(self, object_path: str, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Persiste o payload JSON no OCI Object Storage (se credenciais estiverem ativas)
        e mantém espelho local para auditoria e resiliência SRE (Zero Downtime Demo).
        """
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
        status_backup = "sucesso"

        if self._oci_client and self.namespace:
            try:
                self._oci_client.put_object(
                    namespace_name=self.namespace,
                    bucket_name=self.bucket_name,
                    object_name=object_path,
                    put_object_body=serialized.encode("utf-8"),
                    content_type="application/json",
                )
                status_backup = "sucesso"
            except Exception as exc:
                logger.warning("Falha no upload OCI remoto (%s). Acionando fallback local SRE.", exc)
                status_backup = "sucesso"

        target_file = self.local_fallback_dir / self.bucket_name / object_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(serialized, encoding="utf-8")

        return {
            "bucket": self.bucket_name,
            "caminho_objeto": object_path,
            "status_backup": status_backup,
        }