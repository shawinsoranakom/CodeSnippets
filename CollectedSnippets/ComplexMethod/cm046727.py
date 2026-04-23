def llm_generate_dataset_warning(
    issues: list[str],
    dataset_name: Optional[str] = None,
    modality: str = "text",
    column_names: Optional[list[str]] = None,
) -> Optional[str]:
    """
    Ask the helper LLM to turn technical dataset issues into a user-friendly warning.

    Works for all modalities (text, vision, audio).

    Args:
        issues: List of technical issue descriptions found during analysis.
        dataset_name: Optional HF dataset name.
        modality: "text", "vision", or "audio".
        column_names: Optional list of column names for context.

    Returns:
        A human-friendly warning string, or None on failure.
    """
    if not issues:
        return None

    issues_text = "\n".join(f"- {issue}" for issue in issues)
    cols_text = f"\nColumns: {column_names}" if column_names else ""

    prompt = (
        "You are a helpful assistant. A user is trying to fine-tune a model on a dataset.\n"
        "The following issues were found during dataset analysis:\n\n"
        f"{issues_text}\n\n"
        f"Dataset: {dataset_name or 'unknown'}\n"
        f"Modality: {modality}"
        f"{cols_text}\n\n"
        "Write a brief, friendly explanation of what's wrong and what the user can do about it.\n"
        "Keep it under 3 sentences. Be specific about the dataset."
    )

    result = _run_with_helper(prompt, max_tokens = 200)
    if not result:
        return None

    warning = result.strip()
    # Reject obviously bad outputs
    if len(warning) < 10 or len(warning) > 500:
        return None

    logger.info(f"LLM-generated warning: {warning}")
    return warning