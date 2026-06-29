"""Lógica de cruzamento da sequence 'Teste' do UiPath.

Para cada linha do resultado extraído do Sesmo:
  - normaliza o identificador (tira o prefixo 'CPF: ')
  - se o status indicar falha ('Falha' ou 'não existente'),
    procura a linha correspondente na fila (por CPF ou por nome)
    e marca para escrever F='Revisão', G=<status>.
"""
from __future__ import annotations

from excel_io import LinhaFila

# Termos de status que indicam que a linha precisa de revisão (espelha o If do UiPath)
TERMOS_FALHA = ("Falha", "não existente")


def normalizar_identificador(nome_ou_cpf: str) -> str:
    """Remove o prefixo 'CPF: ' quando presente (igual ao UiPath)."""
    valor = (nome_ou_cpf or "").strip()
    if "CPF" in valor:
        valor = valor.replace("CPF: ", "")
    return valor


def indica_falha(status: str) -> bool:
    s = status or ""
    return any(termo in s for termo in TERMOS_FALHA)


def cruzar(resultado_sesmo: list[tuple[str, str]],
           linhas_fila: list[LinhaFila]) -> list[tuple[int, str]]:
    """Cruza o resultado do Sesmo com a fila.

    resultado_sesmo: lista de (nome_ou_cpf, status) extraída da tabela do Sesmo.
    linhas_fila: linhas lidas da planilha de fila.

    Retorna lista de (excel_row, status) para marcar como 'Revisão'.
    """
    marcacoes: list[tuple[int, str]] = []
    for nome_ou_cpf_raw, status_raw in resultado_sesmo:
        ident = normalizar_identificador(nome_ou_cpf_raw)
        status = (status_raw or "").strip()
        if not indica_falha(status):
            continue
        for linha in linhas_fila:
            if linha.cpf.strip() == ident or linha.colaborador.strip() == ident:
                marcacoes.append((linha.excel_row, status))
                break  # equivalente ao Break do UiPath
    return marcacoes
