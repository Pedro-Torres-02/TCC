# Fluxo Sesmo em Python (migração do UiPath)

Migra para Python a parte **Sesmo Web** do robô (sequence "Teste" do `Main.xaml`
+ a importação de planilhas que não existia no UiPath). O eSocial (Processar Fila
2220/2240) continua no UiPath por enquanto.

## Fluxo
1. Abre o Chrome e faz login no Sesmo (`sesmo.py`)
2. Para cada fila (2220, 2240): importa a planilha no Sesmo, extrai a tabela de
   resultado, cruza com a planilha de fila e marca `F=Revisão` / `G=status`
   nas linhas com falha (`matching.py`, `excel_io.py`)
3. Envia os resultados ao Dash (`dash_envio.py`)

## Arquivos
| Arquivo | Papel | Status |
|---|---|---|
| `config.py` | caminhos e credenciais (lê `.env`) | ✅ |
| `excel_io.py` | leitura da fila + escrita de Revisão/status | ✅ |
| `matching.py` | lógica de cruzamento da sequence "Teste" | ✅ |
| `dash_envio.py` | monta JSON e envia ao dash | ✅ (falta confirmar destino) |
| `selectors.py` | seletores do Sesmo | ⚠️ **TODO — preencher ao vivo** |
| `sesmo.py` | login + importação + extração (Selenium) | ⚠️ depende de `selectors.py` |
| `main.py` | orquestrador | ✅ |

## Setup
```bash
cd python_sesmo
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # e preencha credenciais/caminhos
python main.py
```

## Pendências (precisam de inspeção ao vivo do Sesmo)
- Preencher todos os `TODO` em `selectors.py` (login, importação, tabela de resultado)
- Confirmar a navegação de menu até a tela de importação
- Confirmar o destino do dash (chamar `uipath_bridge.py` ou POST direto)
