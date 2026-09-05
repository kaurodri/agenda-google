"""Operações de CRUD sobre agendas (calendários) do Google Calendar.

Distinção importante da API:
  - `calendars`: a agenda em si — o dono pode criar, editar metadados e deletar.
  - `calendarList`: a lista de agendas visíveis na UI do usuário (inclui a `primary` e agendas
    de terceiros que ele segue). Usamos só para `listar_calendarios`, porque ela já traz todas
    as agendas visíveis com metadados úteis (id, summary, accessRole, se é a primária).

Todas as funções recebem um `service` já autenticado (ver `agenda.auth.get_service`).
"""

TIMEZONE_PADRAO = "America/Sao_Paulo"


def criar_calendario(service, summary, description=None, timezone=TIMEZONE_PADRAO):
    """Cria uma agenda secundária nova, da qual o usuário passa a ser dono."""
    body = {"summary": summary, "timeZone": timezone}
    if description:
        body["description"] = description
    return service.calendars().insert(body=body).execute()


def definir_cor_calendario(service, calendar_id, color_id):
    """Define a cor de uma agenda na paleta do Google Calendar (1 a 24).

    A cor é uma propriedade do `calendarListEntry` (como a agenda aparece na SUA lista),
    não do recurso `calendars` em si — por isso usamos `calendarList().patch()`, não
    `calendars().patch()`. Use `service.colors().get()` para ver a paleta completa
    (background/foreground de cada `colorId`).
    """
    return (
        service.calendarList()
        .patch(calendarId=calendar_id, body={"colorId": str(color_id)})
        .execute()
    )


def listar_calendarios(service):
    """Lista todas as agendas visíveis para o usuário (primária + secundárias + compartilhadas)."""
    resultado = service.calendarList().list().execute()
    return resultado.get("items", [])


def obter_calendario(service, calendar_id):
    """Busca os metadados (summary, description, timeZone) de uma agenda."""
    return service.calendars().get(calendarId=calendar_id).execute()


def atualizar_calendario(service, calendar_id, **campos):
    """Atualiza parcialmente uma agenda (patch) — só altera os campos informados.

    Campos aceitos: summary, description, timezone.

    Nota: `patch` consome mais unidades de cota por chamada do que um `update` completo.
    Aceitável aqui porque só recebemos os campos que o usuário quer alterar; em um cenário de
    atualização em lote de muitas agendas, prefira `get` + `update` completo.
    """
    body = {}
    if campos.get("summary") is not None:
        body["summary"] = campos["summary"]
    if campos.get("description") is not None:
        body["description"] = campos["description"]
    if campos.get("timezone") is not None:
        body["timeZone"] = campos["timezone"]

    return service.calendars().patch(calendarId=calendar_id, body=body).execute()


def deletar_calendario(service, calendar_id):
    """Deleta permanentemente uma agenda que o usuário possui.

    Usa `calendars().delete()` (apaga de fato), não `calendarList().delete()` (que apenas
    removeria a agenda da lista visível do usuário, sem apagá-la).

    Bloqueia a agenda `primary` antes de chamar a API, com uma mensagem clara — a API também
    recusaria essa operação, mas com um erro HTTP menos amigável.
    """
    if calendar_id == "primary":
        raise ValueError(
            "Não é possível deletar a agenda 'primary'. Só agendas secundárias criadas por "
            "você podem ser deletadas."
        )
    service.calendars().delete(calendarId=calendar_id).execute()
