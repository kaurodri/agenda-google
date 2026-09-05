#!/usr/bin/env python3
"""CLI para automatizar a Google Agenda: criar, listar, consultar, editar e deletar eventos.

Exemplos:
    python agenda.py create --summary "Reunião" --start 2026-09-01T10:00:00 --end 2026-09-01T11:00:00
    python agenda.py list --max-results 5
    python agenda.py get --event-id <id>
    python agenda.py update --event-id <id> --summary "Novo título"
    python agenda.py delete --event-id <id>

    python agenda.py calendar create --summary "Faculdade" --description "Aulas e provas"
    python agenda.py calendar list
    python agenda.py calendar get --calendar-id <id>
    python agenda.py calendar update --calendar-id <id> --summary "Faculdade 2026"
    python agenda.py calendar delete --calendar-id <id>
"""

import argparse
import sys

from googleapiclient.errors import HttpError

from agenda.auth import get_service
from agenda.calendarios import (
    atualizar_calendario,
    criar_calendario,
    definir_cor_calendario,
    deletar_calendario,
    listar_calendarios,
    obter_calendario,
)
from agenda.eventos import (
    atualizar_evento,
    criar_evento,
    deletar_evento,
    listar_eventos,
    mover_evento,
    obter_evento,
)


def _formatar_evento(evento):
    inicio = evento.get("start", {}).get("dateTime", evento.get("start", {}).get("date", "?"))
    return f"{evento['id']}  {inicio}  {evento.get('summary', '(sem título)')}"


def cmd_create(service, args):
    evento = criar_evento(
        service,
        summary=args.summary,
        start=args.start,
        end=args.end,
        description=args.description,
        location=args.location,
        attendees=args.attendees,
        calendar_id=args.calendar_id,
        recurrence=args.recurrence,
    )
    print(f"Evento criado: {_formatar_evento(evento)}")
    print(f"Link: {evento.get('htmlLink')}")


def cmd_list(service, args):
    eventos = listar_eventos(
        service,
        calendar_id=args.calendar_id,
        max_results=args.max_results,
        time_min=args.time_min,
    )
    if not eventos:
        print("Nenhum evento encontrado.")
        return
    for evento in eventos:
        print(_formatar_evento(evento))


def cmd_get(service, args):
    evento = obter_evento(service, args.event_id, calendar_id=args.calendar_id)
    print(_formatar_evento(evento))
    if evento.get("description"):
        print(f"Descrição: {evento['description']}")
    if evento.get("location"):
        print(f"Local: {evento['location']}")


def cmd_update(service, args):
    evento = atualizar_evento(
        service,
        args.event_id,
        calendar_id=args.calendar_id,
        summary=args.summary,
        description=args.description,
        location=args.location,
        start=args.start,
        end=args.end,
        attendees=args.attendees,
    )
    print(f"Evento atualizado: {_formatar_evento(evento)}")


def cmd_delete(service, args):
    deletar_evento(service, args.event_id, calendar_id=args.calendar_id)
    print(f"Evento {args.event_id} deletado.")


def cmd_move(service, args):
    evento = mover_evento(
        service, args.event_id, args.destination, calendar_id=args.calendar_id
    )
    print(f"Evento movido: {_formatar_evento(evento)}")


def _formatar_calendario(calendario, primaria=None):
    marca = " (primária)" if primaria else ""
    return f"{calendario['id']}  {calendario.get('summary', '(sem título)')}{marca}"


def cmd_calendar_create(service, args):
    calendario = criar_calendario(
        service, summary=args.summary, description=args.description
    )
    if args.color_id:
        definir_cor_calendario(service, calendario["id"], args.color_id)
    print(f"Agenda criada: {_formatar_calendario(calendario)}")


def cmd_calendar_list(service, args):
    calendarios = listar_calendarios(service)
    if not calendarios:
        print("Nenhuma agenda encontrada.")
        return
    for calendario in calendarios:
        print(_formatar_calendario(calendario, primaria=calendario.get("primary")))


def cmd_calendar_get(service, args):
    calendario = obter_calendario(service, args.calendar_id)
    print(_formatar_calendario(calendario))
    if calendario.get("description"):
        print(f"Descrição: {calendario['description']}")
    print(f"Timezone: {calendario.get('timeZone')}")


def cmd_calendar_update(service, args):
    calendario = atualizar_calendario(
        service,
        args.calendar_id,
        summary=args.summary,
        description=args.description,
        timezone=args.timezone,
    )
    if args.color_id:
        definir_cor_calendario(service, args.calendar_id, args.color_id)
    print(f"Agenda atualizada: {_formatar_calendario(calendario)}")


def cmd_calendar_delete(service, args):
    deletar_calendario(service, args.calendar_id)
    print(f"Agenda {args.calendar_id} deletada.")


def montar_parser():
    parser = argparse.ArgumentParser(description="Automação da Google Agenda via CLI.")
    parser.add_argument(
        "--calendar-id", default="primary", help="ID da agenda (padrão: 'primary')."
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_create = subparsers.add_parser("create", help="Cria um novo evento.")
    p_create.add_argument("--summary", required=True, help="Título do evento.")
    p_create.add_argument("--start", required=True, help="Início em ISO 8601, ex: 2026-09-01T10:00:00")
    p_create.add_argument("--end", required=True, help="Fim em ISO 8601, ex: 2026-09-01T11:00:00")
    p_create.add_argument("--description", help="Descrição do evento.")
    p_create.add_argument("--location", help="Local do evento.")
    p_create.add_argument("--attendees", nargs="*", help="Lista de e-mails dos convidados.")
    p_create.add_argument("--recurrence", nargs="*", help="Lista de RRULE (ex: RRULE:FREQ=WEEKLY;BYDAY=MO)")
    p_create.set_defaults(func=cmd_create)

    p_list = subparsers.add_parser("list", help="Lista os próximos eventos.")
    p_list.add_argument("--max-results", type=int, default=10, help="Número máximo de eventos.")
    p_list.add_argument("--time-min", help="Data/hora mínima em ISO 8601 (padrão: agora).")
    p_list.set_defaults(func=cmd_list)

    p_get = subparsers.add_parser("get", help="Consulta um evento pelo id.")
    p_get.add_argument("--event-id", required=True, help="ID do evento.")
    p_get.set_defaults(func=cmd_get)

    p_update = subparsers.add_parser("update", help="Atualiza campos de um evento.")
    p_update.add_argument("--event-id", required=True, help="ID do evento.")
    p_update.add_argument("--summary", help="Novo título.")
    p_update.add_argument("--start", help="Novo início em ISO 8601.")
    p_update.add_argument("--end", help="Novo fim em ISO 8601.")
    p_update.add_argument("--description", help="Nova descrição.")
    p_update.add_argument("--location", help="Novo local.")
    p_update.add_argument("--attendees", nargs="*", help="Nova lista de e-mails dos convidados.")
    p_update.set_defaults(func=cmd_update)

    p_delete = subparsers.add_parser("delete", help="Deleta um evento pelo id.")
    p_delete.add_argument("--event-id", required=True, help="ID do evento.")
    p_delete.set_defaults(func=cmd_delete)

    p_move = subparsers.add_parser(
        "move", help="Move um evento (ou série recorrente) para outra agenda."
    )
    p_move.add_argument("--event-id", required=True, help="ID do evento (use o id-base para mover a série toda).")
    p_move.add_argument("--destination", required=True, help="ID da agenda de destino.")
    p_move.set_defaults(func=cmd_move)

    p_calendar = subparsers.add_parser("calendar", help="Gerencia agendas (calendários).")
    calendar_subparsers = p_calendar.add_subparsers(dest="calendar_comando", required=True)

    pc_create = calendar_subparsers.add_parser("create", help="Cria uma nova agenda.")
    pc_create.add_argument("--summary", required=True, help="Nome da agenda.")
    pc_create.add_argument("--description", help="Descrição da agenda.")
    pc_create.add_argument(
        "--color-id", help="ID da cor na paleta do Google Calendar (1-24, ex: 17 = lavanda)."
    )
    pc_create.set_defaults(func=cmd_calendar_create)

    pc_list = calendar_subparsers.add_parser("list", help="Lista todas as agendas visíveis.")
    pc_list.set_defaults(func=cmd_calendar_list)

    pc_get = calendar_subparsers.add_parser("get", help="Consulta uma agenda pelo id.")
    pc_get.add_argument("--calendar-id", required=True, help="ID da agenda.")
    pc_get.set_defaults(func=cmd_calendar_get)

    pc_update = calendar_subparsers.add_parser("update", help="Atualiza campos de uma agenda.")
    pc_update.add_argument("--calendar-id", required=True, help="ID da agenda.")
    pc_update.add_argument("--summary", help="Novo nome.")
    pc_update.add_argument("--description", help="Nova descrição.")
    pc_update.add_argument("--timezone", help="Novo timezone (ex: America/Sao_Paulo).")
    pc_update.add_argument(
        "--color-id", help="ID da cor na paleta do Google Calendar (1-24, ex: 17 = lavanda)."
    )
    pc_update.set_defaults(func=cmd_calendar_update)

    pc_delete = calendar_subparsers.add_parser(
        "delete", help="Deleta uma agenda (não é possível deletar a 'primary')."
    )
    pc_delete.add_argument("--calendar-id", required=True, help="ID da agenda.")
    pc_delete.set_defaults(func=cmd_calendar_delete)

    return parser


def main():
    parser = montar_parser()
    args = parser.parse_args()

    try:
        service = get_service()
        args.func(service, args)
    except FileNotFoundError as e:
        print(f"Erro de configuração: {e}", file=sys.stderr)
        sys.exit(1)
    except HttpError as e:
        print(f"Erro na chamada à Google Calendar API: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
