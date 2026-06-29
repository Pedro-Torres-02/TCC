"""Prepara a planilha de Importação de Matrícula a partir da Fila.

Fluxo:
  1. Lê a planilha Fila (Plan1)
  2. Filtra apenas as linhas com status "Sucesso" na coluna F
  3. Escreve na planilha Importação Matrícula via Excel COM (win32com),
     preservando todo o formato original do arquivo:
       Fila col C (CNPJ)      → Importação col A
       Fila col B (CPF)       → Importação col B
       Fila col H (Matrícula) → Importação col C
       Fila col I (Situação)  → Importação col D
"""
from __future__ import annotations

import logging
import os

import config
from excel_io import LinhaFila, ler_fila

log = logging.getLogger("preparar_importacao")

STATUS_SUCESSO = "sucesso"


def _e_sucesso(status: str) -> bool:
    return STATUS_SUCESSO in status.lower()


def _escrever_com_excel(caminho: str, sheet_name: str, sucessos: list[LinhaFila]) -> None:
    """Abre o arquivo com o Excel real via COM e escreve só os valores das células.

    Usar win32com preserva tabelas, formatação, validação de dados e qualquer
    metadado interno que o openpyxl descartaria ao salvar.
    Requer pywin32 (`pip install pywin32`).
    """
    import win32com.client  # noqa: PLC0415

    caminho_abs = os.path.abspath(caminho)
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = None
    try:
        wb = excel.Workbooks.Open(caminho_abs)
        ws = wb.Sheets(sheet_name)
        # Linha 1 = cabeçalho — dados começam na linha 2
        for i, linha in enumerate(sucessos, start=2):
            ws.Cells(i, 1).Value = str(linha.cnpj)       # col A
            ws.Cells(i, 2).Value = str(linha.cpf)        # col B
            ws.Cells(i, 3).Value = str(linha.matricula)  # col C
            ws.Cells(i, 4).Value = str(linha.situacao)   # col D
        wb.Save()
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        excel.Quit()


def preparar(fila: config.FilaConfig) -> int:
    """Preenche a planilha de Importação Matrícula com os dados de sucesso da Fila.

    Retorna o número de linhas escritas.
    """
    caminho_fila = fila.plan_fila
    caminho_import = fila.plan_importacao_matricula
    sheet_import = config.SHEET_IMPORTACAO_MATRICULA

    log.info("[%s] Lendo fila: %s", fila.nome, caminho_fila)
    linhas = ler_fila(caminho_fila)

    sucessos: list[LinhaFila] = [l for l in linhas if _e_sucesso(l.status)]
    log.info("[%s] %d linha(s) com status Sucesso encontradas.", fila.nome, len(sucessos))

    if not sucessos:
        log.warning("[%s] Nenhuma linha com Sucesso — planilha de importação não alterada.", fila.nome)
        return 0

    log.info("[%s] Escrevendo em: %s (sheet '%s')", fila.nome, caminho_import, sheet_import)
    _escrever_com_excel(str(caminho_import), sheet_import, sucessos)
    log.info("[%s] Importação Matrícula preenchida com %d linha(s).", fila.nome, len(sucessos))
    return len(sucessos)


def preparar_todas() -> None:
    """Executa a preparação para todas as filas configuradas (2220 e 2240)."""
    for fila in config.FILAS:
        try:
            preparar(fila)
        except Exception:
            log.exception("[%s] Erro ao preparar importação.", fila.nome)
