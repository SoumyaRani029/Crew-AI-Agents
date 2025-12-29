import streamlit as st
import re

from main import run_all_agents, run_specific_agent, run_with_orchestrator, run_with_orchestrator_multi

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Agents UI", page_icon="🤖", layout="wide")

st.title("Agents UI (Streamlit)")


def to_plain_text(value) -> str:
    """Convert likely-Markdown content to readable plain text for display."""
    text = str(value or "")
    # Remove code fences
    text = re.sub(r"```[\s\S]*?```", lambda m: re.sub(r"^```.*\n|```$", "", m.group(0), flags=re.MULTILINE), text)
    # Inline code backticks
    text = text.replace("`", "")
    # Images ![alt](url) -> alt (url)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1 (\2)", text)
    # Links [text](url) -> text (url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    # Bold/italic markers **text** *text* __text__ _text_
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    # Headings starting with #, #### -> just the text
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    # Blockquotes
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # List markers - *, -, +, and numbered lists
    text = re.sub(r"^\s*[-*+]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", lambda m: f"{m.group(0)}", text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r"^\s*([-*_]){3,}\s*$", "", text, flags=re.MULTILINE)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

with st.sidebar:
    st.header("Mode")
    mode = st.radio(
        "Choose run mode",
        options=["Orchestrate", "All agents", "Force agent"],
        index=0,
    )

    force_role = None
    if mode == "Force agent":
        force_role = st.selectbox("Agent", ["Researcher", "Writer", "Summarizer", "Reviewer", "Emailer"], index=0)

prompt = st.text_area(
    "Prompt",
    value="",
    height=120,
    placeholder="Enter your request (research/write/summarize/review ...)",
)

run_clicked = st.button("Run", type="primary")

if run_clicked:
    if not prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Running..."):
            try:
                if mode == "All agents":
                    result = run_all_agents(prompt)
                    st.subheader("Results (All Agents)")
                    for role, content in result.items():
                        with st.expander(role, expanded=True):
                            st.text(to_plain_text(content))

                elif mode == "Force agent" and force_role:
                    result = run_specific_agent(prompt, force_role)
                    st.subheader(f"Result ({force_role})")
                    for role, content in result.items():
                        with st.expander(role, expanded=(role == force_role)):
                            st.text(to_plain_text(content))

                else:
                    # Orchestrate: detect explicit roles and run them; otherwise fall back
                    result = run_with_orchestrator_multi(prompt, 4)
                    # Show selected roles plus remaining as "Not selected"
                    all_roles = ["Researcher", "Writer", "Summarizer", "Reviewer", "Emailer", "Email Delivery"]
                    chosen_roles = [r for r in all_roles if r in result]
                    subtitle = ", ".join(chosen_roles) if chosen_roles else "None"
                    st.subheader(f"Results (Roles: {subtitle})")
                    for role in all_roles:
                        content = result.get(role, "Not selected")
                        with st.expander(role, expanded=(role in chosen_roles)):
                            st.text(to_plain_text(content))

            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")
# st.caption("Powered by crewai. Ensure OPENAI_API_KEY and SMTP settings are set in your .env.")



