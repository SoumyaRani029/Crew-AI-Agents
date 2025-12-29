from crewai import Agent
from email_agent import emailer

researcher = Agent(
    role="Researcher",
    goal="Conduct in-depth research on given topics",
    backstory="An expert researcher who finds detailed and reliable information.",
    allow_delegation=False
)

writer = Agent(
    role="Writer",
    goal="Create engaging and well-structured content",
    backstory="A skilled writer who can produce articles and blogs.",
    allow_delegation=False
)

summarizer = Agent(
    role="Summarizer",
    goal="Summarize long texts into concise points",
    backstory="A summarizer who converts big text into short insights.",
    allow_delegation=False
)

reviewer = Agent(
    role="Reviewer",
    goal="Review content for accuracy and clarity",
    backstory="An experienced reviewer ensuring correctness and readability.",
    allow_delegation=False
)

orchestrator = Agent(
    role="Orchestrator",
    goal="Decide the most appropriate agent (Researcher, Writer, Summarizer, Reviewer) for a given user prompt.",
    backstory="A seasoned coordinator that understands task requirements and picks the best specialist agent.",
    allow_delegation=False
)