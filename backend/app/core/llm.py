from openai import AsyncOpenAI

from app.core.config import settings


def get_llm_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key or "placeholder",
    )


def get_model_name() -> str:
    return settings.llm_model


AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "add_job",
            "description": "Add a job application to the tracker.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {"type": "string", "description": "Company name"},
                    "role": {"type": "string", "description": "Job role title"},
                    "platform": {"type": "string", "description": "linkedin, indeed, email, or other"},
                    "job_url": {"type": "string", "description": "Direct URL to the job posting"},
                    "notes": {"type": "string", "description": "Extra context about this application"},
                },
                "required": ["company", "role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_job_status",
            "description": "Update a job's status when the situation changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "integer", "description": "ID of the job record"},
                    "new_status": {"type": "string", "description": "applied, under_review, interview, declined, accepted, or no_response"},
                },
                "required": ["job_id", "new_status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_inbox",
            "description": "Fetch unread or recent Gmail messages for the job search inbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail search query. Default: is:unread"},
                    "max_results": {"type": "integer", "description": "How many messages to fetch (default 20)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_thread",
            "description": "Read the full thread of a Gmail conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string", "description": "Gmail thread ID"},
                },
                "required": ["thread_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send a composed email. Draft it first and let me approve unless approval_required is false.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Plain text email body"},
                    "thread_id": {"type": "string", "description": "Gmail thread ID if replying to a thread"},
                    "approval_required": {"type": "boolean", "description": "If true, show draft for user approval. Default true."},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_profile",
            "description": "Save or update a piece of your job search profile (name, email, skills, resume text, answer to screening questions, etc).",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Profile key, e.g. 'name', 'email', 'skills', 'resume_summary', 'screening_answers'"},
                    "value": {"type": "string", "description": "The value to store"},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_profile",
            "description": "Retrieve stored profile data. Call with no arguments to get everything, or with a key to get a specific value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Specific profile key to retrieve, or omit for all"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stats",
            "description": "Get dashboard statistics: total applied, replied, interview, etc.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_to_job",
            "description": "Attempt to apply to a job URL using browser automation. Requires browser login first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL of the job to apply to"},
                    "answers": {
                        "type": "object",
                        "description": "Dict mapping field names (email, phone, name, etc) to values to fill",
                        "additionalProperties": {"type": "string"},
                    },
                    "approval_required": {"type": "boolean", "description": "If true, stop before submit for user approval. Default true."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_job_page",
            "description": "Fetch and read the content of a job posting page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL of the job posting"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_follow_up",
            "description": "Set a follow-up reminder for a job application.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "integer", "description": "Job ID to follow up on"},
                    "when": {"type": "string", "description": "ISO datetime when to follow up"},
                },
                "required": ["job_id", "when"],
            },
        },
    },
]


SYSTEM_PROMPT_BASE = """You are JobBot, an autonomous job-hunting assistant.

Your job is to help the user apply to jobs, manage their inbox, and give them clear status updates.

You have access to tools that let you act. When the user gives you a task, plan it, break it into steps, and execute them using the tools available to you.

Rules:
- Always draft before sending. When approval_required is true (the default), tell the user what you are about to do and ask for confirmation before calling the action tool.
- Be conversational but concise.
- When summarizing email threads, focus on the action items and deadlines.
- Track all applications you create. Give the user regular stats when asked.
- If a job application fails or you hit a login wall, explain what happened and what the user needs to do next.
- Never send an email or apply to a job without mentioning what you are doing first.
- You have a memory of the user's profile. Use it to fill forms and personalize emails. If profile data is missing, ask the user for it and save it.

Current date: {current_date}

You have been given access to the user's Gmail (if connected) and browser (if logged into job platforms).

When you act, always explain what you are doing in a brief status update before and after execution.
"""

BUILTIN_ACTION_TOOLS = {"add_job", "update_job_status", "send_email", "apply_to_job", "save_profile", "schedule_follow_up"}