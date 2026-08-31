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

## Estrutura

- `agenda/auth.py` — autenticação OAuth 2.0 (`get_service()`).
- `agenda/eventos.py` — funções de CRUD reutilizáveis (`criar_evento`, `listar_eventos`,
  `obter_evento`, `atualizar_evento`, `deletar_evento`), podem ser importadas em outros scripts.
- `agenda.py` — CLI (argparse) que expõe essas funções por linha de comando.
