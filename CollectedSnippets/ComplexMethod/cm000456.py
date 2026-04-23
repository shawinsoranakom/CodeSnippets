def _build_email_index(
    submissions: list[dict], questions: list[dict]
) -> dict[str, dict]:
    """Build an {email -> submission_data} index from submissions.

    Scans question titles for email/contact fields to find the email answer.
    """
    # Find question IDs that are likely email fields
    email_question_ids: list[str] = []
    for q in questions:
        label = (q.get("label") or q.get("title") or q.get("name") or "").lower()
        q_type = (q.get("type") or "").lower()
        if q_type in ("input_email", "email"):
            email_question_ids.append(q["id"])
        elif any(kw in label for kw in ("email", "e-mail", "contact")):
            email_question_ids.append(q["id"])

    index: dict[str, dict] = {}
    for sub in submissions:
        email = _extract_email_from_submission(sub, email_question_ids)
        if email:
            index[email.lower()] = {
                "responses": sub.get("responses", sub.get("fields", [])),
                "submitted_at": sub.get("submittedAt", sub.get("createdAt", "")),
                "questions": sub.get("questions", []),
            }
    return index