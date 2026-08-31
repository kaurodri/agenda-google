"""Autenticação OAuth 2.0 com a Google Calendar API.

Fluxo:
  1. Se existir `token.json`, carrega as credenciais salvas.
  2. Se estiverem expiradas mas tiverem refresh_token, renova automaticamente.
  3. Caso contrário, dispara o fluxo OAuth no navegador usando `credentials.json`
     (client secret tipo "Desktop app" gerado no Google Cloud Console).
  4. Salva/atualiza `token.json` para não precisar logar de novo nas próximas execuções.
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Escopo completo de leitura/escrita de eventos.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(_BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(_BASE_DIR, "token.json")


def get_credentials():
    """Carrega credenciais válidas, renovando ou autenticando via navegador se preciso."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Não encontrei '{CREDENTIALS_PATH}'. Baixe o client secret OAuth "
                    "(tipo Desktop app) no Google Cloud Console e coloque na raiz do projeto."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds


def get_service():
    """Retorna um client autenticado da Google Calendar API v3."""
    creds = get_credentials()
    return build("calendar", "v3", credentials=creds)
