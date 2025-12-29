import sys, os
import re
from crewai import Crew

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import agents
from agents import researcher, writer, summarizer, reviewer, emailer

# Import task builder
from task import (
    get_all_role_tasks,
    decide_role_with_orchestrator,
    decide_roles_with_orchestrator,
    detect_roles_from_text,
    extract_email_addresses,
)

from email_agent import send_email, format_email
from config import SMTP_FROM

# Removed keyword routing (run_task)
def to_plain_text(value) -> str:
    """Convert likely-Markdown content to readable plain text for email/UI."""
    text = str(value or "")
    # Remove fenced code blocks but keep inner text
    text = re.sub(r"```[\s\S]*?```", lambda m: re.sub(r"^```.*\n|```$", "", m.group(0), flags=re.MULTILINE), text)
    # Inline code
    text = text.replace("`", "")
    # Images ![alt](url) -> alt (url)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1 (\2)", text)
    # Links [text](url) -> text (url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    # Bold/italic markers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    # Headings
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    # Blockquotes
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # List markers normalization
    text = re.sub(r"^\s*[-*+]\s+", "- ", text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r"^\s*([-*_]){3,}\s*$", "", text, flags=re.MULTILINE)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def run_all_agents(user_input: str):
    role_to_agent = {
        "Researcher": researcher,
        "Writer": writer,
        "Summarizer": summarizer,
        "Reviewer": reviewer,
        "Emailer": emailer,
    }

    role_to_task = get_all_role_tasks(user_input)

    outputs = {}
    for role, agent in role_to_agent.items():
        crew = Crew(agents=[agent], tasks=[role_to_task[role]])
        outputs[role] = crew.kickoff()

    return outputs


def run_with_orchestrator(user_input: str):
    role = decide_role_with_orchestrator(user_input)
    if role is None:
        return {"Error": "Orchestrator could not decide a role."}

    return run_specific_agent(user_input, role)


def run_with_orchestrator_multi(user_input: str, num_roles: int):
    explicit_roles = detect_roles_from_text(user_input)
    roles = explicit_roles if explicit_roles else decide_roles_with_orchestrator(user_input, num_roles)

    recipients = extract_email_addresses(user_input)
    if not roles:
        return {"Error": "Orchestrator could not decide roles."}

    role_to_agent = {
        "Researcher": researcher,
        "Writer": writer,
        "Summarizer": summarizer,
        "Reviewer": reviewer,
        "Emailer": emailer,
    }

    role_to_task = get_all_role_tasks(user_input)
    outputs = {}
    for role in roles:
        if role not in role_to_agent:
            continue
        agent = role_to_agent[role]
        task = role_to_task[role]
        crew = Crew(agents=[agent], tasks=[task])
        outputs[role] = crew.kickoff()

    if "Emailer" in roles or recipients:
        if recipients:
            # Build formatted email using sections
            sections = []
            # Sanitizer to drop unwanted boilerplate/headers/credentials from agent outputs
            def _sanitize(text: str) -> str:
                import re as _re
                unwanted_exact = {
                    "this concludes the structured research brief.",
                }
                patterns = [
                    r"^subject\s*:.*$",
                    r"^to\s*:.*$",
                    r"^body\s*:.*$",
                    r"^dear\s+.+,$",
                    r"^best\s+regards,?\s*$",
                    r"^email content\s*:.*$",
                    r"^contact\s*$",
                    r"^to\s+send\s+this\s+.*email.*$",
                    r"smtp_[a-z_]+\s*=.*",
                    r"imap_[a-z_]+\s*=.*",
                    r"openai_api_key\s*=.*",
                ]
                compiled = [_re.compile(pat, flags=_re.IGNORECASE) for pat in patterns]
                lines = [ln for ln in str(text).split("\n")]
                filtered: list[str] = []
                skip_until_blank = False
                trigger_block = _re.compile(r"^to\s+send\s+this\s+.*email.*$", _re.IGNORECASE)
                for ln in lines:
                    raw = ln.rstrip("\r")
                    if skip_until_blank:
                        if not raw.strip():
                            skip_until_blank = False
                        continue
                    if not raw.strip():
                        continue
                    if raw.strip().lower() in unwanted_exact:
                        continue
                    if trigger_block.search(raw):
                        skip_until_blank = True
                        continue
                    if any(rx.search(raw) for rx in compiled):
                        continue
                    # remove placeholder-only lines like [Your Name]
                    if _re.fullmatch(r"\[[^\]]+\]", raw.strip()):
                        continue
                    filtered.append(raw)
                # collapse extra whitespace
                return "\n".join(filtered).strip()
            for r in ["Researcher", "Writer", "Summarizer", "Reviewer"]:
                if r in outputs:
                    plain = to_plain_text(_sanitize(outputs[r]))
                    sections.append((f"=== {r} ===", plain))

            draft_subject = "Requested topic results"
            email_draft = str(outputs.get("Emailer", ""))
            for line in email_draft.splitlines():
                if line.lower().startswith("subject:"):
                    draft_subject = line.split(":", 1)[1].strip() or draft_subject
                    break

            # Infer sender name from configured SMTP_FROM
            def infer_name_from_email(addr: str) -> str:
                raw = (addr or "").split("@")[0]
                # Replace separators with space, drop numbers, title-case
                cleaned = " ".join(
                    part for part in re_split(r"[._-]+", raw) if part and not part.isdigit()
                )
                words = [w for w in cleaned.split() if w]
                if not words:
                    return addr or "Sender"
                return " ".join(w.capitalize() for w in words)

            # Local regex split helper (no global import side-effects)
            import re as _re
            def re_split(pattern: str, text: str):
                return _re.split(pattern, text)

            sender_name = infer_name_from_email(SMTP_FROM)

            subject, body = format_email(
                subject=draft_subject,
                greeting="Dear Recipient,",
                sections=sections,
                closing="Best regards,",
                signature_lines=[sender_name, SMTP_FROM],
            )

            outputs["Email Delivery"] = send_email(subject=subject, body=body, to_addresses=recipients)
        else:
            outputs["Email Delivery"] = "No valid email addresses found in the prompt."
    return outputs


def run_specific_agent(user_input: str, role: str):
    role_to_agent = {
        "Researcher": researcher,
        "Writer": writer,
        "Summarizer": summarizer,
        "Reviewer": reviewer,
        "Emailer": emailer,
    }

    if role not in role_to_agent:
        return {"Error": f"Unknown agent '{role}'. Choose one of: Researcher, Writer, Summarizer, Reviewer, Emailer."}

    role_to_task = get_all_role_tasks(user_input)
    agent = role_to_agent[role]
    task = role_to_task[role]

    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()

    # Match single-agent output format (all roles with placeholders)
    outputs = {r: (result if r == role else "Not related to this agent") for r in role_to_agent.keys()}
    return outputs


if __name__ == "__main__":
    # Simple CLI when no input files are provided
    args = sys.argv[1:]
    run_all = False
    force_agent = None
    use_orchestrator = True

    # Simple manual args parsing
    i = 0
    collected = []
    while i < len(args):
        if args[i] == "--all":
            run_all = True
            i += 1
        elif args[i] == "--agent" and i + 1 < len(args):
            force_agent = args[i + 1]
            i += 2
        elif args[i] == "--orchestrate":
            use_orchestrator = True
            i += 1
        else:
            collected.append(args[i])
            i += 1

    if sum([1 if run_all else 0, 1 if force_agent else 0, 1 if use_orchestrator else 0]) > 1:
        print("Choose only one mode: --all OR --agent <Role> OR --orchestrate.")
        sys.exit(1)

    if run_all:
        output = run_all_agents(user_input)
        print("\n=== Final Outputs (All Agents) ===")
        for role, response in output.items():
            print(f"{role}: {response}")
    else:
        # Prepare input
        if collected:
            user_input = " ".join(collected)
        else:
            prompt = "Enter your request: " if not force_agent else "Topic to run for the specified agent: "
            user_input = input(prompt)

        if collected and collected[0] == "--send-formatted" and len(collected) >= 3:
            # Usage: --send-formatted "RecipientEmail" "Subject" "Body..."
            to_addr = collected[1]
            subj = collected[2]
            body = " ".join(collected[3:]) if len(collected) > 3 else ""
            print(send_email(subj, body, to_addr))
        elif use_orchestrator:
            output = run_with_orchestrator_multi(user_input, 5)
        elif force_agent:
            output = run_specific_agent(user_input, force_agent.capitalize())
        else:
            output = run_with_orchestrator_multi(user_input, 5)
        print("\n=== Final Outputs ===")
        for role, response in output.items():
            print(f"{role}: {response}")
