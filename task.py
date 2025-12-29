from crewai import Task, Crew
from agents import researcher, writer, summarizer, reviewer, orchestrator, emailer
import re

def get_task(input_text):
    original_text = input_text
    input_text = input_text.lower()

    # Keyword aliases (include some common typos)
    has_research = any(k in input_text for k in ["research", "reseach", "reaearch", "investigate", "explore"]) 
    has_write = any(k in input_text for k in ["write", "article", "draft", "compose"]) 
    has_summarize = any(k in input_text for k in ["summarize", "summary", "summarise", "summerize"]) 
    has_review = any(k in input_text for k in ["review", "critique", "evaluate"]) 
    has_email = any(k in input_text for k in ["email", "e-mail", "mail", "send mail", "send email", "send a mail", "send to", "mail to"]) 

    if has_research:
        return Task(
            description=(
                f"You are the Researcher. Conduct thorough, factual research on the topic below.\n"
                f"- Provide structured sections with bullet points.\n"
                f"- Cite key sources or references (titles/links if known).\n"
                f"- Avoid writing prose articles; focus on findings.\n\n"
                f"Topic: {original_text}"
            ),
            agent=researcher,
            expected_output=(
                "A structured research brief with key findings, evidence, and sources."
            ),
        ), "Researcher"

    if has_write:
        return Task(
            description=(
                f"You are the Writer. Create an engaging, well-structured article based on the topic below.\n"
                f"- Include a clear intro, body with subheadings, and a conclusion.\n"
                f"- Maintain a cohesive narrative; do not list bullets only.\n\n"
                f"Topic: {original_text}"
            ),
            agent=writer,
            expected_output=(
                "A polished article (500-800 words) with headings and clear flow."
            ),
        ), "Writer"

    if has_summarize:
        return Task(
            description=(
                f"You are the Summarizer. Produce a concise summary of the topic below.\n"
                f"- Capture only the most important points.\n"
                f"- Use short bullet points and keep it under 150 words.\n\n"
                f"Topic: {original_text}"
            ),
            agent=summarizer,
            expected_output=(
                "A bullet-point summary under 150 words highlighting key takeaways."
            ),
        ), "Summarizer"

    if has_review:
        return Task(
            description=(
                f"You are the Reviewer. Critically review the content/topic below.\n"
                f"- Identify strengths, weaknesses, and potential improvements.\n"
                f"- Provide 3-5 actionable suggestions.\n\n"
                f"Subject: {original_text}"
            ),
            agent=reviewer,
            expected_output=(
                "A concise review with strengths, weaknesses, and 3-5 concrete improvements."
            ),
        ), "Reviewer"

    if has_email:
        return Task(
            description=(
                f"You are the Emailer. Draft a concise, professional email based on the user's request and any prior content.\n"
                f"- Include a clear subject line.\n"
                f"- Keep the body brief with key points.\n"
                f"- Close with an appropriate sign-off.\n\n"
                f"Prompt: {original_text}"
            ),
            agent=emailer,
            expected_output=(
                "A subject line and short email body ready to be sent."
            ),
        ), "Emailer"

    return None, None


# Builders for running a specific role on demand with the same prompt
def build_research_task(original_text: str) -> Task:
    return Task(
        description=(
            f"You are the Researcher. Conduct thorough, factual research on the topic below.\n"
            f"- Provide structured sections with bullet points.\n"
            f"- Cite key sources or references (titles/links if known).\n"
            f"- Avoid writing prose articles; focus on findings.\n\n"
            f"Topic: {original_text}"
        ),
        agent=researcher,
        expected_output=(
            "A structured research brief with key findings, evidence, and sources."
        ),
    )


def build_writer_task(original_text: str) -> Task:
    return Task(
        description=(
            f"You are the Writer. Create an engaging, well-structured article based on the topic below.\n"
            f"- Include a clear intro, body with subheadings, and a conclusion.\n"
            f"- Maintain a cohesive narrative; do not list bullets only.\n\n"
            f"Topic: {original_text}"
        ),
        agent=writer,
        expected_output=(
            "A polished article (500-800 words) with headings and clear flow."
        ),
    )


def build_summarizer_task(original_text: str) -> Task:
    return Task(
        description=(
            f"You are the Summarizer. Produce a concise summary of the topic below.\n"
            f"- Capture only the most important points.\n"
            f"- Use short bullet points and keep it under 150 words.\n\n"
            f"Topic: {original_text}"
        ),
        agent=summarizer,
        expected_output=(
            "A bullet-point summary under 150 words highlighting key takeaways."
        ),
    )


def build_reviewer_task(original_text: str) -> Task:
    return Task(
        description=(
            f"You are the Reviewer. Critically review the content/topic below.\n"
            f"- Identify strengths, weaknesses, and potential improvements.\n"
            f"- Provide 3-5 actionable suggestions.\n\n"
            f"Subject: {original_text}"
        ),
        agent=reviewer,
        expected_output=(
            "A concise review with strengths, weaknesses, and 3-5 concrete improvements."
        ),
    )


def build_emailer_task(original_text: str) -> Task:
    return Task(
        description=(
            f"You are the Emailer. Draft a concise, professional email based on the user's request and any prior content.\n"
            f"- Include a clear subject line.\n"
            f"- Keep the body brief with key points.\n"
            f"- Close with an appropriate sign-off.\n\n"
            f"Prompt: {original_text}"
        ),
        agent=emailer,
        expected_output=(
            "A subject line and short email body ready to be sent."
        ),
    )


def get_all_role_tasks(original_text: str):
    return {
        "Researcher": build_research_task(original_text),
        "Writer": build_writer_task(original_text),
        "Summarizer": build_summarizer_task(original_text),
        "Reviewer": build_reviewer_task(original_text),
        "Emailer": build_emailer_task(original_text),
    }


def decide_role_with_orchestrator(original_text: str) -> str | None:
    """Use the Orchestrator agent (LLM) to choose the best role name.

    Returns one of: Researcher, Writer, Summarizer, Reviewer, Emailer; or None.
    """
    decision_task = Task(
        description=(
            "You are the Orchestrator. Decide which single role should handle the user's request.\n"
            "Valid roles: Researcher, Writer, Summarizer, Reviewer, Emailer.\n"
            "Return only the role name with no extra words.\n\n"
            f"User request: {original_text}"
        ),
        agent=orchestrator,
        expected_output="One of: Researcher | Writer | Summarizer | Reviewer | Emailer"
    )

    crew = Crew(agents=[orchestrator], tasks=[decision_task])
    raw = crew.kickoff()
    if not raw:
        return None
    text = str(raw).strip()
    for role in ["Researcher", "Writer", "Summarizer", "Reviewer", "Emailer"]:
        if role.lower() in text.lower():
            return role
    return None


def decide_roles_with_orchestrator(original_text: str, num_roles: int) -> list[str]:
    """Use the Orchestrator to pick up to num_roles distinct roles.

    Returns a list containing any of: Researcher, Writer, Summarizer, Reviewer, Emailer.
    """
    num = max(1, min(5, int(num_roles)))
    decision_task = Task(
        description=(
            "You are the Orchestrator. Choose the top roles that should work on the user's request.\n"
            "Valid roles: Researcher, Writer, Summarizer, Reviewer, Emailer.\n"
            "Return only the role names, comma-separated, no extra words.\n"
            f"Number of roles to return: {num}\n\n"
            f"User request: {original_text}"
        ),
        agent=orchestrator,
        expected_output="Comma-separated list of roles from: Researcher, Writer, Summarizer, Reviewer, Emailer"
    )

    crew = Crew(agents=[orchestrator], tasks=[decision_task])
    raw = crew.kickoff()
    if not raw:
        return []
    text = str(raw)
    possible = ["Researcher", "Writer", "Summarizer", "Reviewer", "Emailer"]
    roles: list[str] = []
    for token in [t.strip() for t in text.replace("\n", ",").split(",") if t.strip()]:
        for role in possible:
            if token.lower() == role.lower() and role not in roles:
                roles.append(role)
                break
        if len(roles) >= num:
            break
    return roles


def detect_roles_from_text(original_text: str) -> list[str]:
    """Detect roles explicitly requested in the user text by keywords.

    Returns a list of unique roles in order: Researcher, Writer, Summarizer, Reviewer, Emailer.
    """
    text = (original_text or "").lower()
    role_flags = {
        "Researcher": any(k in text for k in ["research", "researcher"]),
        "Writer": any(k in text for k in ["write","writer"]),
        "Summarizer": any(k in text for k in ["summarize", "summary", "summarise", "summerize", "summarizer"]),
        "Reviewer": any(k in text for k in ["review","reviewer"]) ,
        "Emailer": any(k in text for k in ["email", "e-mail", "mail", "send mail", "send email", "send a mail"]) ,
    }
    ordered = ["Researcher", "Writer", "Summarizer", "Reviewer", "Emailer"]
    return [r for r in ordered if role_flags[r]]


def extract_email_addresses(original_text: str) -> list[str]:
    """Extract likely email addresses from free text.

    Returns a list of emails found; empty if none.
    """
    if not original_text:
        return []
    pattern = r"[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-.]+"
    return re.findall(pattern, original_text)