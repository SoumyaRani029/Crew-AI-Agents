<<<<<<< HEAD
# Agents Project

A multi-agent workflow built with crewai. It supports research, writing, summarization, reviewing, and email delivery (SMTP send). You can run it via a Streamlit UI or a CLI.

## Features
- Research, Write, Summarize, Review, and Email agents
- Orchestrator chooses roles automatically (or force specific role)
- Consolidates multi-agent output into a single formatted email
- SMTP sending with a simple CLI helper

## Requirements
- Python 3.10+
- OpenAI-compatible API key (for crewai LLMs)

Recommended packages (if not already installed):
```bash
pip install -U crewai streamlit python-dotenv
```

## Project Structure
```
D:\Algoleap\Agents\
  agents.py        # Agent definitions (Researcher, Writer, Summarizer, Reviewer, Emailer)
  task.py          # Task builders, Orchestrator helpers, email extraction
  main.py          # Orchestration (all/one/multi), CLI helpers, email formatting+send
  email_agent.py   # SMTP send and format_email helper
  config.py        # Loads .env (OPENAI_API_KEY, SMTP_*)
  app.py           # Streamlit UI
```

## Configuration (.env)
Create a `.env` in the project root with:
```
OPENAI_API_KEY=sk-...

# SMTP (sending)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_email@gmail.com

```
Notes for Gmail:
- Use an App Password if you have 2FA enabled

## Run the Streamlit UI
```bash
streamlit run app.py
```
- Enter a prompt and choose a mode:
  - All agents
  - Force agent (select one of: Researcher, Writer, Summarizer, Reviewer, Emailer)
  - Orchestrate (auto-select roles)
- If your prompt contains an email address, the app formats all available agent outputs into a single email and sends it.

## CLI Usage
Run one of the modes (mutually exclusive):
```bash
python main.py -- --all
python main.py -- --agent Writer "Write about renewable energy policy"
python main.py -- --orchestrate "Research and summarize topic X and email results to name@example.com"
```

### Send a formatted email directly
```bash
python main.py -- "--send-formatted" "recipient@example.com" "Subject here" "Body goes here"
```



## How Email Is Composed
- `main.py` gathers outputs from selected agents and builds sections
- `email_agent.format_email()` creates a standardized body:
  - greeting
  - one block per agent section
  - closing + signature lines
- `email_agent.send_email()` sends via SMTP


## Architecture Diagram (Mermaid)
```mermaid
flowchart TD
  UI[Streamlit UI (app.py)] -->|User prompt + mode| ORCH[Orchestrator (main.py)]
  CLI[CLI (python main.py ...)] --> ORCH

  subgraph Main[main.py]
    ORCH -->|--all| ALL[run_all_agents]
    ORCH -->|--agent <Role>| ONE[run_specific_agent]
    ORCH -->|--orchestrate| MULTI[run_with_orchestrator_multi]
    ORCH -->|--send-formatted| SENDCLI[send_email]
  end

  subgraph Tasks[task.py]
    DETECT[detect_roles_from_text]
    BUILD[get_all_role_tasks]
    EXTRACT[extract_email_addresses]
  end

  subgraph Agents[agents.py]
    R[Researcher]
    W[Writer]
    S[Summarizer]
    RV[Reviewer]
    E[Emailer]
  end

  subgraph Email[email_agent.py]
    FMT[format_email]
    SEND[send_email (SMTP)]
  end

  CFG[config.py]

  ORCH --> BUILD
  ORCH --> DETECT
  ORCH --> EXTRACT
  ALL --> R & W & S & RV & E
  ONE --> R & W & S & RV & E
  MULTI --> R & W & S & RV & E

  R --> OUTS[Aggregate Outputs]
  W --> OUTS
  S --> OUTS
  RV --> OUTS
  E --> DRAFT[Optional subject hints]

  OUTS --> FMT
  DRAFT --> FMT
  EXTRACT --> FMT
  FMT --> SEND
  SEND --> STATUS[Email Delivery Status]

  SENDCLI --> SEND

  CFG -.-> Main
  CFG -.-> Email
  CFG -.-> Agents
```

## Troubleshooting
- SMTP not configured: Ensure all SMTP_* vars are set; check firewall/VPN
- Gmail: Use an App Password; enable “Less secure apps” is deprecated—use App Passwords

- Streamlit import error after code changes: click “Rerun” in the UI

## Security
- Do not commit `.env` with real credentials
- Use dedicated app passwords and restricted accounts where possible

## License
MIT
=======
# Crew-AI-Agents
>>>>>>> f08b1214194dc69e2b65c9dc6afe1f125281d5a9
