"""Operações de CRUD sobre eventos da Google Agenda.

Todas as funções recebem um `service` já autenticado (ver `agenda.auth.get_service`)
e podem ser importadas e usadas diretamente em outros scripts Python, além de
serem usadas pela CLI (`agenda.py`).
"""

TIMEZONE_PADRAO = "America/Sao_Paulo"

# Campos que fazem sentido replicar ao copiar um evento para outra conta/agenda. Propositalmente
# fora daqui: id, etag, iCalUID, htmlLink, created, updated, organizer, creator, sequence, status,
# kind (pertencem ao evento original/à conta de origem) e attendees (para não reenviar convites a
# quem já foi convidado no evento original).
CAMPOS_COPIAVEIS = [
    "summary",
    "description",
    "location",
    "start",
    "end",
    "recurrence",
    "reminders",
    "colorId",
    "transparency",
    "visibility",
]


def _montar_evento(
    summary,
    start,
    end,
    description=None,
    location=None,
    attendees=None,
    timezone=TIMEZONE_PADRAO,
    recurrence=None,
):
    evento = {
        "summary": summary,
        "start": {"dateTime": start, "timeZone": timezone},
        "end": {"dateTime": end, "timeZone": timezone},
    }
    if description:
        evento["description"] = description
    if location:
        evento["location"] = location
    if attendees:
        evento["attendees"] = [{"email": email} for email in attendees]
    if recurrence:
        evento["recurrence"] = recurrence
    return evento


def criar_evento(
    service,
    summary,
    start,
    end,
    description=None,
    location=None,
    attendees=None,
    calendar_id="primary",
    timezone=TIMEZONE_PADRAO,
    recurrence=None,
):
    """Cria um evento novo. `start`/`end` em ISO 8601, ex: 2026-09-01T10:00:00.

    `recurrence` é uma lista de strings RRULE, ex: ["RRULE:FREQ=WEEKLY;BYDAY=MO"]
    """
    body = _montar_evento(
        summary, start, end, description, location, attendees, timezone, recurrence
    )
    return service.events().insert(calendarId=calendar_id, body=body).execute()


def listar_eventos(service, calendar_id="primary", max_results=10, time_min=None):
    """Lista os próximos eventos, ordenados por horário de início.

    `time_min` em ISO 8601 com timezone (ex: 2026-09-01T00:00:00Z). Se omitido,
    usa o horário atual.
    """
    if time_min is None:
        import datetime

        time_min = datetime.datetime.now(datetime.timezone.utc).isoformat()

    resultado = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return resultado.get("items", [])


def obter_evento(service, event_id, calendar_id="primary"):
    """Busca um evento específico pelo id."""
    return service.events().get(calendarId=calendar_id, eventId=event_id).execute()


def atualizar_evento(service, event_id, calendar_id="primary", **campos):
    """Atualiza parcialmente um evento (patch) — só altera os campos informados.

    Campos aceitos: summary, description, location, start, end, timezone, attendees.
    """
    body = {}
    if "summary" in campos and campos["summary"] is not None:
        body["summary"] = campos["summary"]
    if "description" in campos and campos["description"] is not None:
        body["description"] = campos["description"]
    if "location" in campos and campos["location"] is not None:
        body["location"] = campos["location"]

    timezone = campos.get("timezone") or TIMEZONE_PADRAO
    if campos.get("start"):
        body["start"] = {"dateTime": campos["start"], "timeZone": timezone}
    if campos.get("end"):
        body["end"] = {"dateTime": campos["end"], "timeZone": timezone}
    if campos.get("attendees"):
        body["attendees"] = [{"email": email} for email in campos["attendees"]]

    return (
        service.events()
        .patch(calendarId=calendar_id, eventId=event_id, body=body)
        .execute()
    )


def deletar_evento(service, event_id, calendar_id="primary"):
    """Deleta um evento pelo id."""
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()


def mover_evento(service, event_id, destino_calendar_id, calendar_id="primary"):
    """Move um evento (ou uma série recorrente inteira, se `event_id` for o id-base) de uma
    agenda para outra, ambas do mesmo usuário. Usa `events().move()`."""
    return (
        service.events()
        .move(calendarId=calendar_id, eventId=event_id, destination=destino_calendar_id)
        .execute()
    )


def copiar_evento(
    origem_service,
    destino_service,
    event_id,
    origem_calendar_id="primary",
    destino_calendar_id="primary",
):
    """Copia um evento de uma agenda para outra em **contas Google diferentes**.

    Diferente de `mover_evento` (que usa `events().move()` e só funciona dentro da mesma conta),
    aqui lemos o evento na origem e criamos um evento equivalente na conta de destino — por isso
    recebe dois `service` diferentes, um autenticado em cada conta (ver `agenda.auth.get_service`).

    Só os campos em `CAMPOS_COPIAVEIS` são replicados — não copia convidados (attendees), para
    não reenviar convites a quem já foi convidado no evento original. `start`/`end` são copiados
    como vieram da API (incluindo `timeZone`), preservando o horário correto na conta de destino.

    Limitação conhecida: se o evento original for uma série recorrente com exceções (ex: uma
    ocorrência específica cancelada ou remarcada), a série copiada nasce "limpa", sem essas
    exceções — só a RRULE base é copiada.
    """
    evento = (
        origem_service.events()
        .get(calendarId=origem_calendar_id, eventId=event_id)
        .execute()
    )
    body = {campo: evento[campo] for campo in CAMPOS_COPIAVEIS if campo in evento}
    return destino_service.events().insert(calendarId=destino_calendar_id, body=body).execute()
