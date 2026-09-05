# agenda-google

CLI em Python para automatizar tarefas na Google Agenda: criar, listar, consultar, editar e deletar eventos.

## Configuração

1. **Credenciais OAuth**: baixe o `credentials.json` (client secret tipo "Desktop app") no
   [Google Cloud Console](https://console.cloud.google.com/apis/credentials), com a Calendar API
   habilitada, e coloque-o na raiz do projeto (`agenda-google/credentials.json`). Esse arquivo é
   sensível e já está no `.gitignore` — não faça commit dele. O formato esperado está em
   [`credentials.example.json`](credentials.example.json) — copie e preencha com os seus dados:

   ```bash
   cp credentials.example.json credentials.json
   ```

2. **Ambiente virtual e dependências**:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

3. **Primeiro login**: na primeira execução de qualquer comando, uma janela do navegador vai abrir
   pedindo login e consentimento na sua conta Google. Depois disso, um `token.json` é salvo na raiz
   do projeto e reutilizado automaticamente (renovado sozinho quando expira). Também está no
   `.gitignore` — o formato gerado está documentado em [`token.example.json`](token.example.json),
   mas você não precisa criá-lo manualmente, ele é gerado sozinho.

## Uso

```bash
# Criar um evento
python agenda.py create --summary "Reunião" --start 2026-09-01T10:00:00 --end 2026-09-01T11:00:00

# Listar os próximos eventos
python agenda.py list --max-results 5

# Consultar um evento específico
python agenda.py get --event-id <id>

# Atualizar campos de um evento (só altera o que for informado)
python agenda.py update --event-id <id> --summary "Novo título"

# Deletar um evento
python agenda.py delete --event-id <id>
```

Use `--calendar-id` (antes do subcomando) para operar em uma agenda diferente da principal, ex:
`python agenda.py --calendar-id outra@agenda.com list`.

### Eventos recorrentes

O comando `create` aceita `--recurrence` com uma ou mais regras [RRULE (RFC 5545)](https://icalendar.org/rrule-tool.html).
O `--start`/`--end` definem a data/hora da **primeira** ocorrência — a recorrência repete a
partir dela, então confira o dia da semana correspondente antes de criar.

```bash
# Toda segunda-feira, começando em 31/08/2026 (que é uma segunda-feira)
python agenda.py create --summary "RG Enactus UFU" \
  --start 2026-08-31T18:30:00 --end 2026-08-31T19:30:00 \
  --recurrence "RRULE:FREQ=WEEKLY;BYDAY=MO"

# Toda terça e quinta
python agenda.py create --summary "Treino" \
  --start 2026-09-01T07:00:00 --end 2026-09-01T08:00:00 \
  --recurrence "RRULE:FREQ=WEEKLY;BYDAY=TU,TH"

# Todo dia útil (segunda a sexta)
python agenda.py create --summary "Daily" \
  --start 2026-09-01T09:00:00 --end 2026-09-01T09:15:00 \
  --recurrence "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"

# Todo mês, na primeira segunda-feira
python agenda.py create --summary "Reunião mensal" \
  --start 2026-09-07T18:30:00 --end 2026-09-07T19:30:00 \
  --recurrence "RRULE:FREQ=MONTHLY;BYDAY=1MO"

# Diariamente, com data final (até 31/12/2026)
python agenda.py create --summary "Lembrete diário" \
  --start 2026-09-01T08:00:00 --end 2026-09-01T08:05:00 \
  --recurrence "RRULE:FREQ=DAILY;UNTIL=20261231T235959Z"
```

`list` e `get` mostram cada ocorrência com um id no formato `<id-base>_<data>`; para editar ou
deletar **uma única ocorrência**, use esse id completo. Para editar ou deletar **a série toda**,
use o `<id-base>` (a parte antes do `_`).

## Gerenciar agendas (calendários)

Além de eventos, o CLI também cria, lista, consulta, edita e deleta **agendas** (calendários
secundários no Google Calendar — ex: uma agenda separada para "Faculdade" ou "Trabalho"), com o
subcomando `calendar`:

```bash
# Criar uma agenda nova
python agenda.py calendar create --summary "Faculdade" --description "Aulas e provas"

# Listar todas as agendas visíveis (inclui a "primary" e as secundárias)
python agenda.py calendar list

# Consultar uma agenda pelo id
python agenda.py calendar get --calendar-id <id>

# Atualizar campos de uma agenda (só altera o que for informado)
python agenda.py calendar update --calendar-id <id> --summary "Faculdade 2026"

# Deletar uma agenda
python agenda.py calendar delete --calendar-id <id>
```

Depois de criar uma agenda, use o `id` retornado com `--calendar-id <id>` (antes do subcomando)
nos comandos de evento normais para criar/listar/editar eventos nela:

```bash
python agenda.py --calendar-id <id> create --summary "Prova" --start ... --end ...
```

**Limitações importantes**: só é possível editar ou deletar agendas que você mesmo criou — não a
agenda `primary` (bloqueada explicitamente pelo CLI) nem agendas de terceiros que você apenas
segue. `calendar update` usa uma atualização parcial (`patch`), que consome mais unidades de cota
por chamada do que uma atualização completa — aceitável para uso individual, mas se um dia isso
virar automação em lote de muitas agendas, prefira buscar a agenda inteira (`get`) e reenviar todos
os campos de uma vez.

## Múltiplas contas Google

O CLI suporta gerenciar mais de uma conta Google (ex: pessoal e trabalho). A conta "default" é a
configurada na raiz do projeto (`credentials.json`/`token.json`, o setup descrito acima) — ela é
usada sempre que `--account` não é informado, então tudo que você já usa continua funcionando
exatamente igual. Contas adicionais ficam em `accounts/<email>/`:

```
agenda-google/
├── credentials.json              # conta "default"
├── token.json
└── accounts/
    └── outraconta@gmail.com/
        ├── credentials.json      # client secret OAuth dessa conta
        └── token.json            # gerado no 1º login dessa conta
```

Para configurar uma conta adicional: crie a pasta `accounts/<email-da-conta>/`, baixe o
`credentials.json` (client secret OAuth) no Google Cloud Console — pode ser o mesmo projeto já
usado para a conta default, não precisa criar um projeto novo por e-mail — e coloque nessa pasta
(veja o modelo em [`accounts/example@dominio.com/credentials.example.json`](accounts/example@dominio.com/credentials.example.json)).
O `token.json` é gerado sozinho no primeiro comando rodado com `--account`:

```bash
# Roda o login dessa conta na primeira vez, depois reutiliza o token salvo
python agenda.py --account outraconta@gmail.com list

# Lista as contas configuradas (default + accounts/*), mostrando o e-mail autenticado de cada uma
python agenda.py accounts
```

`--account` funciona com qualquer comando de evento ou agenda já existente (`create`, `list`,
`calendar create`, etc.) — ele só decide qual `credentials.json`/`token.json` usar.

### Copiar eventos entre contas

Diferente do `move` (que só funciona dentro da mesma conta), copiar um evento para **outra conta**
Google exige ler o evento na origem e criar um equivalente na conta de destino — é o que
`copy-event` faz:

```bash
python agenda.py copy-event --event-id <id> \
  --from-account default --from-calendar-id primary \
  --to-account outraconta@gmail.com --to-calendar-id primary
```

**Limitações importantes**:
- **Não copia convidados (attendees)** — evita reenviar convites/notificações a quem já foi
  convidado no evento original. A cópia leva título, horário, local, descrição, recorrência,
  lembretes, cor e visibilidade.
- **Não copia exceções de séries recorrentes** — se o evento original tiver uma ocorrência
  específica cancelada ou remarcada, a série copiada nasce "limpa", só com a regra de recorrência
  base.
- Copia **um evento por vez**. Para copiar muitos eventos (ex: um semestre inteiro), rode o
  comando em loop externamente — assim como já fazemos hoje para criar várias aulas — e tome
  cuidado com os limites de taxa da API em lotes grandes.

## Estrutura

- `agenda/auth.py` — autenticação OAuth 2.0, com suporte a múltiplas contas (`get_service(account=None)`).
- `agenda/eventos.py` — funções de CRUD reutilizáveis (`criar_evento`, `listar_eventos`,
  `obter_evento`, `atualizar_evento`, `deletar_evento`, `mover_evento`, `copiar_evento`), podem ser
  importadas em outros scripts.
- `agenda/calendarios.py` — funções de CRUD de agendas (`criar_calendario`, `listar_calendarios`,
  `obter_calendario`, `atualizar_calendario`, `deletar_calendario`, `definir_cor_calendario`).
- `agenda.py` — CLI (argparse) que expõe essas funções por linha de comando.
