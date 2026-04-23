def _extract_email_from_submission(
    submission: dict, email_question_ids: list[str]
) -> Optional[str]:
    """Extract email address from a submission by checking respondentEmail, then field responses."""
    # Try respondent email first (Tally often includes this)
    respondent_email = submission.get("respondentEmail")
    if respondent_email:
        return respondent_email

    # Search through responses/fields for matching question IDs
    responses = submission.get("responses", submission.get("fields", []))
    if isinstance(responses, list):
        for resp in responses:
            q_id = resp.get("questionId") or resp.get("key") or resp.get("id")
            if q_id in email_question_ids:
                value = resp.get("value") or resp.get("answer")
                if isinstance(value, str) and "@" in value:
                    return value
    elif isinstance(responses, dict):
        for q_id in email_question_ids:
            value = responses.get(q_id)
            if isinstance(value, str) and "@" in value:
                return value

    return None