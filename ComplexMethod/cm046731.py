def llm_conversion_advisor(
    column_names: list[str],
    samples: list[dict],
    dataset_name: Optional[str] = None,
    hf_token: Optional[str] = None,
    model_name: Optional[str] = None,
    model_type: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Full conversion advisor: fetch HF card → multi-pass LLM analysis.

    Falls back to simple llm_classify_columns() if the multi-pass advisor fails.

    Returns:
        Dict with keys: success, suggested_mapping, system_prompt, user_template,
        assistant_template, label_mapping, dataset_type, is_conversational,
        user_notification. Or None on complete failure.
    """
    # Fetch HF dataset card if this looks like a HF dataset (has a slash)
    dataset_card = None
    dataset_metadata = None
    if dataset_name and "/" in dataset_name:
        dataset_card, dataset_metadata = fetch_hf_dataset_card(dataset_name, hf_token)

    # Try multi-pass advisor
    result = _run_multi_pass_advisor(
        columns = column_names,
        samples = samples,
        dataset_name = dataset_name,
        dataset_card = dataset_card,
        dataset_metadata = dataset_metadata,
        model_name = model_name,
        model_type = model_type,
        hf_token = hf_token,
    )

    if result and result.get("success"):
        logger.info(f"Conversion advisor succeeded: type={result.get('dataset_type')}")
        return result

    # Fallback: simple column classification
    logger.info("Advisor failed, falling back to simple column classification")
    simple_mapping = llm_classify_columns(column_names, samples)
    if simple_mapping:
        return {
            "success": True,
            "suggested_mapping": {
                col: role
                for col, role in simple_mapping.items()
                if role in ("user", "assistant", "system")
            },
            "dataset_type": None,
            "is_conversational": None,
            "user_notification": None,
        }

    return None