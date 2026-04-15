"""Claude API batching and resume-relevant extraction from emails."""

import re
import json
import anthropic

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


SYSTEM_PROMPT = """You are a career coach and resume writer. Analyze work emails and extract resume-relevant information.

Focus on:
1. PROJECTS — names, goals, outcomes, deliverables
2. SKILLS & TECHNOLOGIES — languages, tools, platforms, frameworks, methodologies
3. ACHIEVEMENTS — measurable results, metrics, milestones, problems solved
4. RESPONSIBILITIES — roles, leadership, ownership, team coordination
5. COLLABORATIONS — team sizes, departments, clients, stakeholders
6. TIME CONTEXT — approximate dates (helpful for dating resume entries)

Return a JSON object with exactly these keys:
{
  "projects": [{"name": "...", "description": "...", "outcome": "...", "approx_date": "..."}],
  "skills": ["skill1", "skill2"],
  "achievements": ["achievement1"],
  "responsibilities": ["responsibility1"],
  "collaborations": ["context1"],
  "notes": "other resume-relevant observations"
}

Only include clearly resume-relevant items. Skip personal or purely administrative emails.
Return valid JSON only — no text outside the JSON."""


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def get_body(message, max_chars: int) -> str:
    try:
        body = message.plain_text_body
        if body:
            return clean_text(body.decode("utf-8", errors="replace"))[:max_chars]
    except Exception:
        pass
    try:
        body = message.html_body
        if body:
            return clean_text(body.decode("utf-8", errors="replace"))[:max_chars]
    except Exception:
        pass
    return ""


def format_email(folder: str, message, max_body_chars: int) -> str:
    date = ""
    try:
        date = str(message.client_submit_time or "")
    except Exception:
        pass
    return (
        f"Folder: {folder}\n"
        f"Date: {date}\n"
        f"From: {clean_text(message.sender_name or '')}\n"
        f"Subject: {clean_text(message.subject or '')}\n"
        f"Body: {get_body(message, max_body_chars)}\n"
    )


def analyze_batch(batch: list[str], model: str) -> dict:
    """Send a batch of formatted emails to Claude and return structured resume data."""
    combined = "\n\n---\n\n".join(batch)
    response = get_client().messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze these {len(batch)} work emails and extract resume-relevant information:\n\n{combined}",
        }],
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw}
