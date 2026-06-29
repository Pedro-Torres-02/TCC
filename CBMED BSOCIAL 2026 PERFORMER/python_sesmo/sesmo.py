"""Automação do Sesmo Web via Selenium.

Fluxo:
  1. login()          — preenche usuário, senha, lê captcha SVG, faz login
  2. navegar_importar() — eSocial → Configurações → Importar Matrícula
  3. importar_planilha() — envia o arquivo e clica Importar
  4. extrair_resultado() — lê a tabela Nome do Colaborador / Aviso

Os seletores estão em seletores.py.
"""
from __future__ import annotations

import base64
import logging
import os
import re
import time

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
import seletores as sel

log = logging.getLogger("sesmo")


class Sesmo:
    """Encapsula a sessão do navegador no Sesmo Web."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.driver: webdriver.Chrome | None = None

    # -- ciclo de vida --------------------------------------------------------
    @staticmethod
    def _fechar_chrome() -> None:
        """Encerra todos os processos Chrome antes de abrir nova sessão."""
        import subprocess
        subprocess.call(
            ["taskkill", "/F", "/IM", "chrome.exe", "/T"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1)

    def abrir(self) -> None:
        self._fechar_chrome()
        opts = Options()
        if config.HEADLESS:
            opts.add_argument("--headless=new")
        opts.add_argument("--start-maximized")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=opts)
        self.driver.get(config.SESMO_URL)

    def fechar(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __enter__(self):
        self.abrir()
        return self

    def __exit__(self, *exc):
        self.fechar()

    # -- helpers --------------------------------------------------------------
    def _wait(self, timeout: int | None = None):
        return WebDriverWait(self.driver, timeout or self.timeout)

    def _clicar(self, seletor, timeout: int | None = None):
        """Clica no elemento com retry para stale/overlay; usa JS click como último recurso."""
        t = timeout or self.timeout
        interceptado = 0
        for _ in range(5):
            try:
                self._wait(t).until(EC.element_to_be_clickable(seletor)).click()
                return
            except StaleElementReferenceException:
                time.sleep(0.5)
            except ElementClickInterceptedException:
                interceptado += 1
                if interceptado >= 2:
                    # Overlay persistente — JavaScript click bypassa qualquer overlay
                    el = self._wait(t).until(EC.presence_of_element_located(seletor))
                    self.driver.execute_script("arguments[0].click();", el)
                    log.debug("Clique via JS (overlay bloqueou clique normal).")
                    return
                self._aguardar_sem_loading()

    def _digitar(self, seletor, texto: str, timeout: int | None = None):
        el = self._wait(timeout).until(EC.presence_of_element_located(seletor))
        el.clear()
        el.send_keys(texto)

    def _aguardar(self, seletor, timeout: int | None = None):
        return self._wait(timeout).until(EC.presence_of_element_located(seletor))

    def _aguardar_sem_loading(self, timeout: int = 30) -> None:
        """Aguarda o overlay de carregamento do Sesmo sumir.

        O Sesmo usa display:var(--Gnc-loading) — CSS variable que o Selenium não
        consegue avaliar via invisibility_of_element_located. Usa JS para verificar
        o computedStyle real.
        """
        script = (
            "var el = document.querySelector('[data-type=\"Loading-Modal\"]');"
            "if (!el) return true;"
            "var s = window.getComputedStyle(el);"
            "return s.display === 'none' || s.visibility === 'hidden';"
        )
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if self.driver.execute_script(script):
                    return
            except Exception:
                return
            time.sleep(0.4)
        log.warning("Loading modal ainda visível após %ds — continuando mesmo assim.", timeout)

    # -- captcha --------------------------------------------------------------
    def _ler_captcha(self) -> str:
        """Lê o texto do captcha SVG e retorna em minúsculo."""
        img_el = self._aguardar(sel.LOGIN_CAPTCHA_IMG)
        src = img_el.get_attribute("src")
        # src = "data:image/svg+xml;base64,<b64>"
        b64 = src.split(",", 1)[1]
        svg = base64.b64decode(b64).decode("utf-8", errors="replace")
        match = re.search(r">([^<]+)</text>", svg)
        if not match:
            raise RuntimeError(f"Não foi possível extrair texto do captcha SVG: {svg[:200]}")
        return match.group(1).strip().lower()

    # -- fluxo ----------------------------------------------------------------
    def login(self, max_tentativas: int = 3) -> None:
        """Faz login no Sesmo com retry automático em caso de captcha errado."""
        from selenium.common.exceptions import TimeoutException as _TE

        log.info("Fazendo login no Sesmo (%s)...", config.SESMO_URL)
        for tentativa in range(1, max_tentativas + 1):
            self._digitar(sel.LOGIN_USUARIO, config.SESMO_USUARIO)
            self._digitar(sel.LOGIN_SENHA, config.SESMO_SENHA)

            captcha = self._ler_captcha()
            log.info("Captcha lido (tentativa %d/%d): %s", tentativa, max_tentativas, captcha)
            self._digitar(sel.LOGIN_CAPTCHA_INP, captcha)

            self._clicar(sel.LOGIN_BOTAO)
            try:
                self._aguardar(sel.LOGIN_OK, timeout=60)
                log.info("Login OK.")
                return
            except _TE:
                if tentativa == max_tentativas:
                    raise
                log.warning("Login falhou (captcha incorreto?) — aguardando novo captcha e tentando novamente...")
                time.sleep(3)

    def _fechar_modal_se_aberto(self) -> None:
        """Fecha o modal de Importar Matrícula se ainda estiver aberto (entre filas)."""
        try:
            btns = self.driver.find_elements(*sel.IMPORT_BTN_CANCELAR)
            if btns and btns[0].is_displayed():
                btns[0].click()
                time.sleep(1)
        except Exception:
            pass

    def navegar_importar(self) -> None:
        """Navega: eSocial (top) → Configurações (lateral) → Importar Matrícula."""
        self._fechar_modal_se_aberto()
        self._aguardar_sem_loading()
        log.info("Navegando para eSocial → Configurações → Importar Matrícula...")

        # eSocial pode demorar 10–30s para carregar
        self._clicar(sel.MENU_ESOCIAL)
        log.info("Clicou eSocial, aguardando módulo carregar (até 45s)...")
        self._aguardar(sel.MENU_LAT_CONFIGURACOES, timeout=45)
        self._aguardar_sem_loading()

        # Configurações (expande o submenu)
        self._clicar(sel.MENU_LAT_CONFIGURACOES)
        self._aguardar(sel.MENU_LAT_IMPORTAR_MATRICULA)

        # Importar Matrícula
        self._clicar(sel.MENU_LAT_IMPORTAR_MATRICULA)
        self._aguardar_sem_loading()
        self._aguardar(sel.MODAL_IMPORTAR)
        log.info("Modal 'Importar Matrícula' aberto.")

    def importar_planilha(self, caminho_arquivo: str) -> None:
        """Envia o arquivo via send_keys no input[type='file'] e clica em Importar."""
        caminho_abs = os.path.abspath(caminho_arquivo)
        log.info("Enviando arquivo para input[type='file']: %s", caminho_abs)
        file_input = self._aguardar(sel.IMPORT_INPUT_FILE)
        self.driver.execute_script("arguments[0].style.display='block';", file_input)
        file_input.send_keys(caminho_abs)
        val = file_input.get_attribute("value")
        log.info("Valor do file input após send_keys: %s", val)

        log.info("Clicando em Importar...")
        self._clicar(sel.IMPORT_BTN_IMPORTAR)
        log.info("Aguardando importação concluir...")

        # Dá tempo do servidor iniciar o loading antes de verificar
        time.sleep(3)
        self._aguardar_sem_loading(timeout=180)

        # Aguarda pelo menos uma linha aparecer (tabela pode demorar para renderizar)
        log.info("Aguardando tabela de resultado renderizar...")
        try:
            self._wait(180).until(EC.presence_of_element_located(sel.RESULTADO_LINHAS))
            log.info("Tabela detectada.")
        except TimeoutException:
            log.warning("Tabela de resultado não apareceu em 180s — tentando extrair mesmo assim.")

        time.sleep(1)

        # Dump do HTML completo para diagnóstico dos seletores
        try:
            html = self.driver.page_source
            dump_path = os.path.join(os.path.dirname(__file__), "debug_pagina.html")
            with open(dump_path, "w", encoding="utf-8") as f:
                f.write(html)
            log.info("HTML da página salvo em: %s", dump_path)
        except Exception as e:
            log.warning("Não foi possível salvar dump HTML: %s", e)

        log.info("Importação concluída.")

    def extrair_resultado(self) -> list[tuple[str, str]]:
        """Extrai a tabela de resultado: lista de (nome_colaborador, aviso)."""
        log.info("Extraindo tabela de resultado...")

        linhas_els = self.driver.find_elements(*sel.RESULTADO_LINHAS)
        log.debug("Seletor RESULTADO_LINHAS retornou %d linhas.", len(linhas_els))

        resultado: list[tuple[str, str]] = []
        for linha in linhas_els:
            try:
                spans = linha.find_elements(*sel.RESULTADO_CEL_VALOR)
                if len(spans) < 2:
                    continue
                ident  = spans[0].text.strip()
                status = spans[1].text.strip()
                if not ident or not status:
                    continue
            except Exception:
                continue
            resultado.append((ident, status))
        log.info("%d linha(s) extraída(s) do resultado.", len(resultado))
        for ident, status in resultado:
            log.info("  → [%s] | [%s]", ident, status)
        return resultado
