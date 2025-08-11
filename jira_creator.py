import requests
from openai import OpenAI
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
import httpx


OPENAI_API_KEY = ""
client = OpenAI(api_key=OPENAI_API_KEY, http_client=httpx.Client(verify=False))


JIRA_BASE_URL = "https://altimetrik-team-demo.atlassian.net"
JIRA_EMAIL = "sjaswanth@altimetrik.com"
JIRA_API_TOKEN = ""
JIRA_PROJECT_KEY = "DEMO"
JIRA_ISSUE_TYPE = "Task"


class JiraState(BaseModel):
    summary: str
    description: str
    review_required: bool = False
    severity: str = "Unknown"
    status: str = "Unknown"
    issue_key: str = ""


def llm_decide_node(state: JiraState) -> JiraState:
    prompt = f"""
You are a Jira triage assistant. Given the following issue:

Summary:
{state.summary}

Description:
{state.description}

Decide if this issue needs manual review.
Reply only with true or false.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a triage decision bot."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    decision = response.choices[0].message.content.strip().lower()
    needs_review = decision == "true"

    severity = "High" if needs_review else "Low"
    status = "Proceeding to Jira creation." if needs_review else "No review required. Skipping Jira."

    return state.model_copy(update={
        "review_required": needs_review,
        "severity": severity,
        "status": status
    })

def create_jira_ticket_node(state: JiraState) -> JiraState:
    if not state.review_required:
        print("No review required. Skipping Jira.")
        return state.model_copy(update={"status": "No review required. Skipping Jira."})

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": state.summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": state.description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {"name": JIRA_ISSUE_TYPE}
        }
    }

    headers = {"Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    response = requests.post(
        f"{JIRA_BASE_URL}/rest/api/3/issue",
        json=payload,
        headers=headers,
        auth=auth
    )

    if response.status_code == 201:
        key = response.json().get("key")
        print(f"Created Jira issue: {key}")
        return state.model_copy(update={
            "issue_key": key,
            "status": "Jira ticket created successfully."
        })
    else:
        print(f"Jira creation failed: {response.status_code}")
        print("Response:", response.text)
        return state.model_copy(update={
            "status": f"Jira creation failed: {response.status_code}",
            "issue_key": ""
        })

def jira_result_node(state: JiraState) -> JiraState:
    return state

builder = StateGraph(JiraState)
builder.add_node("llm_decide", llm_decide_node)
builder.add_node("create_jira", create_jira_ticket_node)
builder.add_node("jira_result", jira_result_node)
builder.set_entry_point("llm_decide")
builder.add_edge("llm_decide", "create_jira")
builder.add_edge("create_jira", "jira_result")
builder.add_edge("jira_result", END)

app = builder.compile()
