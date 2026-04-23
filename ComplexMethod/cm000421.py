def merge_business_understanding_data(
    existing_data: dict[str, Any],
    input_data: BusinessUnderstandingInput,
) -> dict[str, Any]:
    """Merge new input into existing data dict using incremental strategy.

    - String fields: new value overwrites if provided (not None)
    - List fields: new items are appended to existing (deduplicated)
    - suggested_prompts: fully replaced if provided (not None)

    Returns the merged data dict (mutates and returns *existing_data*).
    """
    existing_business: dict[str, Any] = {}
    if isinstance(existing_data.get("business"), dict):
        existing_business = dict(existing_data["business"])

    business_string_fields = [
        "job_title",
        "business_name",
        "industry",
        "business_size",
        "user_role",
        "additional_notes",
    ]
    business_list_fields = [
        "key_workflows",
        "daily_activities",
        "pain_points",
        "bottlenecks",
        "manual_tasks",
        "automation_goals",
        "current_software",
        "existing_automation",
    ]

    # Handle top-level name field
    if input_data.user_name is not None:
        existing_data["name"] = input_data.user_name

    # Business string fields - overwrite if provided
    for field in business_string_fields:
        value = getattr(input_data, field)
        if value is not None:
            existing_business[field] = value

    # Business list fields - merge with existing
    for field in business_list_fields:
        value = getattr(input_data, field)
        if value is not None:
            existing_list = _json_to_list(existing_business.get(field))
            merged = _merge_lists(existing_list, value)
            existing_business[field] = merged

    # Suggested prompts - fully replace if provided
    if input_data.suggested_prompts is not None:
        existing_data["suggested_prompts"] = input_data.suggested_prompts

    # Set version and nest business data
    existing_business["version"] = 1
    existing_data["business"] = existing_business

    return existing_data