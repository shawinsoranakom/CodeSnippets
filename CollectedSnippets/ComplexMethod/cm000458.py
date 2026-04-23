def format_submission_for_llm(submission: dict, questions: list[dict]) -> str:
    """Format a submission as readable Q&A text for LLM consumption."""
    # Build question ID -> title lookup
    q_titles: dict[str, str] = {}
    for q in questions:
        q_id = q.get("id", "")
        title = q.get("label") or q.get("title") or q.get("name") or f"Question {q_id}"
        q_titles[q_id] = title

    lines: list[str] = []
    responses = submission.get("responses", [])

    if isinstance(responses, list):
        for resp in responses:
            q_id = resp.get("questionId") or resp.get("key") or resp.get("id") or ""
            title = q_titles.get(q_id, f"Question {q_id}")
            value = resp.get("value") or resp.get("answer") or ""
            lines.append(f"Q: {title}\nA: {_format_answer(value)}")
    elif isinstance(responses, dict):
        for q_id, value in responses.items():
            title = q_titles.get(q_id, f"Question {q_id}")
            lines.append(f"Q: {title}\nA: {_format_answer(value)}")

    return "\n\n".join(lines)