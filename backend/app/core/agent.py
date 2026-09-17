from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall

from app.core.llm import BUILTIN_ACTION_TOOLS, SYSTEM_PROMPT_BASE, get_llm_client, get_model_name, AGENT_TOOLS_SCHEMA


async def dispatch_tool_call(tool_name: str, arguments: dict[str, Any], session: Any) -> str:
    from app.tools.tracker import ConversationLog, EmailBox, JobTracker, ProfileStore

    tracker = JobTracker(session)
    email_box = EmailBox(session)
    profile = ProfileStore(session)

    if tool_name == "add_job":
        job = await tracker.add_job(
            company=arguments["company"],
            role=arguments["role"],
            platform=arguments.get("platform", "unknown"),
            job_url=arguments.get("job_url", ""),
            notes=arguments.get("notes", ""),
        )
        return f"Job added with ID {job.id}: {job.company} — {job.role} ({job.platform}), status {job.status}"

    if tool_name == "update_job_status":
        job = await tracker.update_job_status(
            job_id=arguments["job_id"],
            new_status=arguments["new_status"],
        )
        if job is None:
            return "Job not found."
        return f"Job {job.id} ({job.company} — {job.role}) updated to {job.status}"

    if tool_name == "check_inbox":
        import app.tools.gmail as gmail_mod

        query = arguments.get("query", "is:unread")
        max_results = arguments.get("max_results", 20)
        messages = gmail_mod.list_messages(query=query, max_results=max_results)
        for msg in messages:
            await email_box.upsert_email(
                external_id=msg["id"],
                subject=msg.get("subject", ""),
                sender=msg.get("from", ""),
                snippet=msg.get("snippet", ""),
                thread_id=msg.get("thread_id", ""),
            )
        summary_parts = [f"- [{m.get('subject', 'No subject')}] from {m.get('from', '?')}: {m.get('snippet', '')}" for m in messages]
        return f"Found {len(messages)} messages:\n" + "\n".join(summary_parts) if messages else "No messages found."

    if tool_name == "read_thread":
        import app.tools.gmail as gmail_mod

        thread = gmail_mod.get_thread(arguments["thread_id"])
        parts = [f"[{m.get('date', '')}] {m.get('from', '')}:\n{m.get('body', '')}" for m in thread]
        return "\n\n".join(parts) if parts else "Thread is empty."

    if tool_name == "send_email":
        import app.tools.gmail as gmail_mod

        gmail_mod.send_email(
            to=arguments["to"],
            subject=arguments["subject"],
            body=arguments["body"],
            thread_id=arguments.get("thread_id"),
        )
        return f"Email sent to {arguments['subject']}"

    if tool_name == "save_profile":
        await profile.set_value(key=arguments["key"], value=arguments["value"])
        return f"Saved profile key '{arguments['key']}'"

    if tool_name == "get_profile":
        key = arguments.get("key")
        if key:
            value = await profile.get_value(key)
            return f"{key} = {value}" if value else f"No value found for '{key}'"
        all_vals = await profile.all_values()
        if not all_vals:
            return "Profile is empty."
        lines = [f"- {k}: {v[:200]}" for k, v in all_vals.items()]
        return "Profile:\n" + "\n".join(lines)

    if tool_name == "get_stats":
        counts = await tracker.job_status_counts()
        total = sum(counts.values())
        parts = [f"{status}: {count}" for status, count in counts.items()]
        return f"Total applications: {total}\n" + "\n".join(parts)

    if tool_name == "apply_to_job":
        import app.tools.browser as browser_mod

        result = await browser_mod.fill_and_submit_application(
            url=arguments["url"],
            profile_data=arguments.get("answers", {}),
            answers=arguments.get("answers", {}),
            approval_required=arguments.get("approval_required", True),
        )
        if result.get("status") == "needs_login":
            return "The browser is not logged into this platform. Ask the user to run login_interactive and then try again."
        return f"Application attempt: {result.get('status', 'unknown')} — {result.get('message', '')} {result.get('error', '')}"

    if tool_name == "read_job_page":
        import app.tools.browser as browser_mod

        details = await browser_mod.extract_job_details(arguments["url"])
        return f"Title: {details.get('title', '?')}\nCompany: {details.get('company', '?')}\n\n{details.get('description', '')[:2000]}"

    if tool_name == "schedule_follow_up":
        when_dt = datetime.fromisoformat(arguments["when"]).replace(tzinfo=timezone.utc)
        job = await tracker.set_follow_up(arguments["job_id"], when_dt)
        if job is None:
            return "Job not found."
        return f"Follow-up scheduled for {job.company} — {job.role} on {arguments['when']}"

    return f"Unknown tool called: {tool_name}"


async def agent_respond(user_message: str, message_history: list[dict[str, str]], session: Any) -> dict[str, Any]:
    client = get_llm_client()
    model = get_model_name()
    system_prompt = SYSTEM_PROMPT_BASE.format(current_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    full_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    full_messages.extend(message_history)
    full_messages.append({"role": "user", "content": user_message})

    tools_used_this_turn: list[str] = []

    for _ in range(12):
        response = await client.chat.completions.create(
            model=model,
            messages=full_messages,
            tools=AGENT_TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.4,
        )

        choice = response.choices[0]
        assistant_message: ChatCompletionMessage = choice.message

        if assistant_message.tool_calls:
            full_messages.append({"role": "assistant", "content": assistant_message.content or "", "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls]})

            for tool_call in assistant_message.tool_calls:
                fn = tool_call.function
                fn_name = fn.name
                fn_args = {}
                try:
                    import json as _json
                    fn_args = _json.loads(fn.arguments)
                except Exception:
                    pass
                tools_used_this_turn.append(fn_name)
                result_text = await dispatch_tool_call(fn_name, fn_args, session)
                full_messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result_text})
        else:
            return {
                "reply": assistant_message.content or "",
                "tools_used": tools_used_this_turn,
            }

    return {
        "reply": "I reached my action limit this turn. Try again or break your request into a smaller step.",
        "tools_used": tools_used_this_turn,
    }