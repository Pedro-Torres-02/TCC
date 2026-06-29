"""Configuração central do fluxo Sesmo em Python.

Lê caminhos e credenciais do arquivo .env (copie .env.example -> .env).
"""
from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# ---------------------------------------------------------------------------
# Pasta raiz com as planilhas (variável única que muda por máquina/execução)
# ---------------------------------------------------------------------------
PASTA_EXECUTAR = _get(
    "PASTA_EXECUTAR",
    r"C:\Users\cbmed\OneDrive\Documentos\BSOCIAL\CBMED\Executar",
)


def encontrar_arquivo(padrao: str) -> str:
    """Retorna o caminho do arquivo mais recente que corresponde ao padrão glob.

    padrao: relativo a PASTA_EXECUTAR, ex: 'Fila*S2220*.xlsx'
    Levanta FileNotFoundError se nenhum arquivo for encontrado.
    """
    matches = glob.glob(os.path.join(PASTA_EXECUTAR, padrao))
    if not matches:
        raise FileNotFoundError(
            f"Nenhum arquivo encontrado em '{PASTA_EXECUTAR}' com padrão '{padrao}'"
        )
    # Se houver mais de um (execuções antigas), pega o mais recente
    return max(matches, key=os.path.getmtime)


# ---------------------------------------------------------------------------
# Credenciais do Sesmo
# ---------------------------------------------------------------------------
SESMO_URL = _get("SESMO_URL", "https://cbmed.sesmoweb.com.br/")
SESMO_USUARIO = _get("SESMO_USUARIO")
SESMO_SENHA = _get("SESMO_SENHA")

HEADLESS = _get("HEADLESS", "false").lower() in ("1", "true", "sim", "yes")

# ---------------------------------------------------------------------------
# Dash
# ---------------------------------------------------------------------------
DASH_BRIDGE_PATH = _get("DASH_BRIDGE_PATH")
DASH_ENDPOINT = _get("DASH_ENDPOINT")

# ---------------------------------------------------------------------------
# Arquivamento
# ---------------------------------------------------------------------------
PASTA_ARQUIVAR = _get(
    "PASTA_ARQUIVAR",
    r"C:\Users\cbmed\OneDrive\Documentos\BSOCIAL\CBMED\Executadas Inconsistencias",
)

# ---------------------------------------------------------------------------
# Nomes das sheets (verificar se batem com as planilhas reais)
# ---------------------------------------------------------------------------
SHEET_FILA = "Plan1"
SHEET_IMPORTACAO_MATRICULA = _get("SHEET_IMPORTACAO_MATRICULA", "Importação do Colaborador")
SHEET_IMPORTADOS_SESMO = _get("SHEET_IMPORTADOS_SESMO", "Planilha1")


# ---------------------------------------------------------------------------
# Configuração por fila
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FilaConfig:
    nome: str   # "2220" ou "2240"

    # Planilha de acompanhamento (onde temos status, CPF, CNPJ, matrícula, etc.)
    @property
    def plan_fila(self) -> str:
        return encontrar_arquivo(f"Fila*{self.nome}*.xlsx")

    # Planilha que vamos preencher e depois subir no Sesmo
    @property
    def plan_importacao_matricula(self) -> str:
        return encontrar_arquivo(f"*mporta*atricula*{self.nome}*.xlsx")

    # Planilha onde salvamos o resultado extraído do Sesmo
    @property
    def plan_importados_sesmo(self) -> str:
        return encontrar_arquivo(f"*mportados*Sesmo*{self.nome}*.xlsx")


FILAS = [FilaConfig(nome="2220"), FilaConfig(nome="2240")]


def validar_caminhos(fila: FilaConfig) -> list[str]:
    """Tenta resolver os caminhos e retorna lista de erros."""
    problemas: list[str] = []
    for rotulo, padrao in (
        ("plan_fila", f"Fila*{fila.nome}*.xlsx"),
        ("plan_importacao_matricula", f"*mporta*atricula*{fila.nome}*.xlsx"),
        ("plan_importados_sesmo", f"*mportados*Sesmo*{fila.nome}*.xlsx"),
    ):
        try:
            encontrar_arquivo(padrao)
        except FileNotFoundError as e:
            problemas.append(f"[{fila.nome}] {rotulo}: {e}")
    return problemas
