"""Autenticação OAuth 2.0 com a Google Calendar API, com suporte a múltiplas contas.

Fluxo:
  1. Se existir `token.json` da conta, carrega as credenciais salvas.
  2. Se estiverem expiradas mas tiverem refresh_token, renova automaticamente.
  3. Caso contrário, dispara o fluxo OAuth no navegador usando o `credentials.json` da conta
     (client secret tipo "Desktop app" gerado no Google Cloud Console).
  4. Salva/atualiza o `token.json` da conta para não precisar logar de novo nas próximas execuções.

Contas: a conta "default" (ou `None`) usa `credentials.json`/`token.json` na raiz do projeto —
é o comportamento original, para quem só usa uma conta Google. Qualquer outro valor de `account`
(ex: o e-mail da conta) usa os arquivos em `accounts/<account>/credentials.json` e
`accounts/<account>/token.json`, permitindo gerenciar várias contas Google no mesmo CLI. O
`credentials.json` (client secret OAuth) pode ser o mesmo projeto do Cloud Console reaproveitado
entre contas — o que é específico de cada conta é o `token.json`, gerado no login daquele e-mail.
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Escopo completo de leitura/escrita de eventos.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_DIR = os.path.join(_BASE_DIR, "accounts")
CREDENTIALS_PATH = os.path.join(_BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(_BASE_DIR, "token.json")


def _paths_for_account(account=None):
    """Resolve os caminhos de credentials.json/token.json para a conta informada.

    `account` None ou "default" usa os arquivos na raiz (comportamento original).
    """
    if account in (None, "default"):
        return CREDENTIALS_PATH, TOKEN_PATH
    base = os.path.join(ACCOUNTS_DIR, account)
    return os.path.join(base, "credentials.json"), os.path.join(base, "token.json")


def get_credentials(account=None):
    """Carrega credenciais válidas da conta informada, renovando ou autenticando via
    navegador se preciso."""
    credentials_path, token_path = _paths_for_account(account)
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                nome_conta = account or "default"
                raise FileNotFoundError(
                    f"Não encontrei '{credentials_path}' para a conta '{nome_conta}'. Baixe o "
                    "client secret OAuth (tipo Desktop app) no Google Cloud Console e coloque "
                    f"em '{credentials_path}'."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds


def get_service(account=None):
    """Retorna um client autenticado da Google Calendar API v3 para a conta informada."""
    creds = get_credentials(account)
    return build("calendar", "v3", credentials=creds)
