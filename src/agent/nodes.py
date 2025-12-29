from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from src.agent.state import ReviewState
from src.config import settings
from src.github.client import GitHubClient

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm():
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "anthropic":
        return ChatAnthropic(
            model_name=settings.MODEL_NAME,
            api_key=settings.ANTHROPIC_API_KEY
        )
    elif provider == "openai":
        return ChatOpenAI(
            model_name=settings.MODEL_NAME,
            api_key=settings.OPENAI_API_KEY
        )
    elif provider == "google":
        return ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

llm = get_llm()

from src.agent.prompts import ANALYZE_STRUCTURE_SYSTEM_PROMPT, DRAFT_ROADMAP_SYSTEM_PROMPT

def analyze_structure(state: ReviewState) -> dict:
    """Groups files into logical components."""
    print("--- Node: Analyze Structure ---")
    
    files_list = "\n".join([f"- {f.path} ({f.status}, +{f.additions}/-{f.deletions})" for f in state.pr_context.files])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYZE_STRUCTURE_SYSTEM_PROMPT),
        ("human", "PR Title: {title}\n\nFiles:\n{files}")
    ])
    
    # In a real implementation, we'd use structued output. 
    # For now, we'll ask for JSON text and parse it (or use with_structured_output if available/configured).
    # keeping it simple for the skeleton.
    
    chain = prompt | llm
    response = chain.invoke({
        "title": state.pr_context.metadata.title,
        "files": files_list
    })
    
    # Mocking the parsing for safety in this step, ideally we use structured output
    # For V1 let's just store the raw text or try to parse
    return {"topology": {"analysis": response.content}}

def context_expansion(state: ReviewState) -> dict:
    """Decides if we need to fetch more content."""
    print("--- Node: Context Expansion ---")
    # Simple logic: If topology mentions 'high risk' or similar, we might fetch.
    # For V1, we will skip the loop and just proceed to roadmap to get end-to-end working first.
    return {"required_context": []}

def draft_roadmap(state: ReviewState) -> dict:
    """Generates the final Markdown roadmap."""
    print("--- Node: Draft Roadmap ---")
    
    # Prepare File Context with Base Links
    files_context = []
    repo_url = state.pr_context.metadata.repo_url
    pr_number = state.pr_context.metadata.number
    
    for f in state.pr_context.files:
        # Base link for the file (Context for LLM to link to top of file)
        # We start with line 1 so it opens the file in diff view, or just the anchor
        file_link = f.get_pr_diff_link(repo_url, pr_number)
        files_context.append(f"- {f.path} ({f.status}): {file_link}")

    # Prepare Comments Context
    comments_context = []
    for c in state.pr_context.comments:
        location = f"({c.path}:{c.line})" if c.path else "(General)"
        comments_context.append(f"- {c.user} {location}: {c.body}")
    
    context_str = f"""
    Title: {state.pr_context.metadata.title}
    Description: {state.pr_context.metadata.description}
    Author: {state.pr_context.metadata.author}
    Repo URL: {repo_url}
    PR Number: {pr_number}
    
    Topology Analysis:
    {state.topology.get('analysis', 'No analysis')}
    
    Files (with base links):
    {chr(10).join(files_context)}
    
    Existing Comments:
    {chr(10).join(comments_context) if comments_context else "No comments found."}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", DRAFT_ROADMAP_SYSTEM_PROMPT),
        ("human", "{context}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"context": context_str})
    
    return {"roadmap": response.content}
