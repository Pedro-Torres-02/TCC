"""Seletores estáveis do Sesmo Web — mapeados ao vivo em 28/06/2026.

Todos os IDs são dinâmicos (timestamp). Usamos class, placeholder e XPath por texto.
"""
from selenium.webdriver.common.by import By

# ---------------------------------------------------------------------------
# LOGIN (cbmed.sesmoweb.com.br/Account/LogIn)
# ---------------------------------------------------------------------------
LOGIN_USUARIO      = (By.CSS_SELECTOR, "input[placeholder='* Usuário ou E-mail']")
LOGIN_SENHA        = (By.CSS_SELECTOR, "input[type='password']")
LOGIN_CAPTCHA_IMG  = (By.CSS_SELECTOR, "gnc-image img")         # SVG; ler src e decodificar base64
LOGIN_CAPTCHA_INP  = (By.CSS_SELECTOR, "input[placeholder='Digite os caracteres:']")
LOGIN_BOTAO        = (By.CSS_SELECTOR, ".Gnc-Login-BtnEntrar")
# Elemento que confirma login bem-sucedido (menu do dashboard)
LOGIN_OK           = (By.CSS_SELECTOR, ".btnMenuHome")

# ---------------------------------------------------------------------------
# MENU TOP — eSocial
# ---------------------------------------------------------------------------
MENU_ESOCIAL = (By.XPATH, "//div[contains(@class,'btnMenuHome') and normalize-space()='eSocial']")

# ---------------------------------------------------------------------------
# MENU LATERAL (após clicar eSocial)
# ---------------------------------------------------------------------------
MENU_LAT_CONFIGURACOES      = (By.XPATH, "//div[contains(@class,'Gnc-NavBarGroup-V2-Header') and normalize-space()='Configurações']")
MENU_LAT_IMPORTAR_MATRICULA = (By.XPATH, "//div[contains(@class,'Gnc-NavBarItem-V2-Container') and normalize-space()='Importar Matrícula']")

# ---------------------------------------------------------------------------
# MODAL "Importar Matrícula"
# ---------------------------------------------------------------------------
# O modal inteiro — usado como âncora para elementos dentro dele
MODAL_IMPORTAR      = (By.CSS_SELECTOR, ".Gnc-Window-V1-Modal")

# Input file (hidden — usar send_keys diretamente com o caminho absoluto do arquivo)
IMPORT_INPUT_FILE   = (By.CSS_SELECTOR, "input[type='file']")

# Botão que abre o dialog de seleção de arquivo
IMPORT_BTN_ESCOLHER = (By.XPATH, "//button[normalize-space()='Escolher arquivo']")

# Botão que confirma a importação
IMPORT_BTN_IMPORTAR = (By.XPATH, "//button[normalize-space()='Importar']")

# Botão cancelar (para fechar o modal se necessário)
IMPORT_BTN_CANCELAR = (By.XPATH, "//button[normalize-space()='Cancelar']")

# ---------------------------------------------------------------------------
# OVERLAY DE CARREGAMENTO (bloqueia cliques durante transições de página)
# ---------------------------------------------------------------------------
LOADING_MODAL = (By.CSS_SELECTOR, "[data-type='Loading-Modal']")

# ---------------------------------------------------------------------------
# TABELA DE RESULTADO (dentro do modal, após clicar Importar)
# ---------------------------------------------------------------------------
# Estado inicial / sem dados ainda
RESULTADO_SEM_DADOS = (By.XPATH, "//*[contains(text(),'Não Existem registros')]")

# Linhas de dados da grid GNC (não usa <tr><td> — usa divs)
RESULTADO_LINHAS     = (By.CSS_SELECTOR, "[data-type='Grid-Row']")

# Dentro de cada linha: valores em ordem (nome, aviso)
RESULTADO_CEL_VALOR  = (By.CSS_SELECTOR, "span[data-type='Grid-currentValueDiv']")
