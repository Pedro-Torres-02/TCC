"""Orquestrador do fluxo Sesmo em Python.

Etapas (cada uma pode ser executada separadamente passando argumento):
  1. preparar   — lê a Fila, filtra Sucessos, preenche Importação Matrícula (2220 e 2240)
  2. sesmo      — login no Sesmo, importa planilhas, extrai resultado, marca Revisão na Fila
  3. dash       — envia resultados ao dashboard

Uso:
  python main.py              → executa todas as etapas
  python main.py preparar     → só a etapa 1
  python main.py sesmo        → só a etapa 2
  python main.py dash         → só a etapa 3
"""
from __future__ import annotations

import logging
import sys

import arquivar
import config
import dash_envio
import excel_io
import matching
import preparar_importacao

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")


# ---------------------------------------------------------------------------
# Etapa 1: preparar planilhas de importação
# ---------------------------------------------------------------------------
def etapa_preparar() -> None:
    log.info("=== ETAPA 1: Preparar Importação Matrícula ===")
    problemas: list[str] = []
    for fila in config.FILAS:
        problemas += config.validar_caminhos(fila)
    if problemas:
        for p in problemas:
            log.warning(p)

    preparar_importacao.preparar_todas()


# ---------------------------------------------------------------------------
# Etapa 2: Sesmo (login → importar → extrair → marcar Revisão)
# ---------------------------------------------------------------------------
def _processar_fila_sesmo(sesmo: Sesmo, fila: config.FilaConfig) -> None:
    log.info("=== Fila %s ===", fila.nome)

    # Abre o modal "Importar Matrícula" (eSocial → Configurações → Importar Matrícula)
    sesmo.navegar_importar()

    # Importa a planilha de matrícula no Sesmo
    sesmo.importar_planilha(fila.plan_importacao_matricula)

    # Extrai o resultado da tela (lista de (nome_colaborador, aviso))
    resultado = sesmo.extrair_resultado()

    # Salva resultado completo na Planilha Importados Sesmo (col A = nome, col B = aviso)
    excel_io.escrever_importados_sesmo(fila.plan_importados_sesmo, resultado)
    log.info("Fila %s: %d linha(s) salvas em Importados Sesmo.", fila.nome, len(resultado))

    # Cruza apenas os erros com a Fila e marca F='Revisão', G=aviso
    linhas_fila = excel_io.ler_fila(fila.plan_fila)
    marcacoes = matching.cruzar(resultado, linhas_fila)
    excel_io.escrever_revisao(fila.plan_fila, marcacoes)
    log.info("Fila %s: %d linha(s) marcada(s) como Revisão.", fila.nome, len(marcacoes))


def etapa_sesmo() -> None:
    from sesmo import Sesmo  # import lazy — não carrega Selenium nas outras etapas
    log.info("=== ETAPA 2: Sesmo (login + importação + extração) ===")
    with Sesmo() as sesmo:
        sesmo.login()
        for fila in config.FILAS:
            try:
                _processar_fila_sesmo(sesmo, fila)
            except Exception:
                log.exception("Erro ao processar fila %s no Sesmo.", fila.nome)


# ---------------------------------------------------------------------------
# Etapa 3: envio ao dash
# ---------------------------------------------------------------------------
def etapa_dash() -> None:
    log.info("=== ETAPA 3: Envio ao Dash ===")
    for fila in config.FILAS:
        try:
            enviados = dash_envio.enviar_fila(fila.plan_fila, fila.nome)
            log.info("Dash: %d registro(s) enviados (fila %s).", enviados, fila.nome)
        except Exception:
            log.exception("Erro no envio ao dash da fila %s.", fila.nome)


# ---------------------------------------------------------------------------
# Etapa 4: arquivar planilhas executadas
# ---------------------------------------------------------------------------
def etapa_arquivar() -> None:
    log.info("=== ETAPA 4: Arquivar Planilhas Executadas ===")
    try:
        destino = arquivar.arquivar_executar()
        log.info("Planilhas arquivadas em: %s", destino)
    except Exception:
        log.exception("Erro ao arquivar planilhas.")


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------
ETAPAS = {
    "preparar": etapa_preparar,
    "sesmo": etapa_sesmo,
    "dash": etapa_dash,
    "arquivar": etapa_arquivar,
}


def main() -> None:
    args = sys.argv[1:]
    if args:
        for arg in args:
            if arg not in ETAPAS:
                log.error("Etapa desconhecida: '%s'. Opções: %s", arg, list(ETAPAS))
                sys.exit(1)
            ETAPAS[arg]()
    else:
        # Executa tudo em ordem
        etapa_preparar()
        etapa_sesmo()
        etapa_dash()
        etapa_arquivar()


if __name__ == "__main__":
    main()
