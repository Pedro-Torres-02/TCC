"""Move todas as planilhas da pasta Executar para a subpasta de arquivo datada."""
from __future__ import annotations

import glob
import logging
import os
import re
import shutil

import config

log = logging.getLogger("arquivar")


def _extrair_data() -> str:
    """Extrai a data do nome de uma planilha Fila (ex: 'Fila S2220 09.06.2026.xlsx' → '09.06.2026')."""
    padrao = os.path.join(config.PASTA_EXECUTAR, "Fila*.xlsx")
    arquivos = glob.glob(padrao)
    if not arquivos:
        raise FileNotFoundError(f"Nenhuma planilha Fila encontrada em '{config.PASTA_EXECUTAR}'")
    nome = os.path.basename(arquivos[0])
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", nome)
    if not match:
        raise ValueError(f"Não foi possível extrair data do nome: '{nome}'")
    return match.group(1)


def arquivar_executar() -> str:
    """Move todos os .xlsx da pasta Executar para PASTA_ARQUIVAR/<data>.

    Retorna o caminho da subpasta criada.
    """
    data = _extrair_data()
    destino = os.path.join(config.PASTA_ARQUIVAR, data)
    os.makedirs(destino, exist_ok=True)
    log.info("Subpasta de destino: %s", destino)

    arquivos = glob.glob(os.path.join(config.PASTA_EXECUTAR, "*.xlsx"))
    if not arquivos:
        log.warning("Nenhum arquivo .xlsx encontrado em '%s'.", config.PASTA_EXECUTAR)
        return destino

    for origem in arquivos:
        nome = os.path.basename(origem)
        shutil.move(origem, os.path.join(destino, nome))
        log.info("Movido: %s → %s", nome, destino)

    log.info("%d arquivo(s) movido(s) para '%s'.", len(arquivos), destino)
    return destino
