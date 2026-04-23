def _verify_trackio_args(training_args: "TrainingArguments") -> None:
    """Validates Trackio-specific arguments.

    Args:
        training_args: TrainingArguments instance (not a dictionary)
    """
    report_to = training_args.report_to
    if not report_to:
        return

    if isinstance(report_to, str):
        report_to = [report_to]

    if "trackio" not in report_to:
        return

    # --- Enforce project (required by Trackio) ---
    if not training_args.project:
        raise ValueError("`--project` must be specified when using Trackio.")

    # --- Validate trackio_space_id format ---
    space_id = training_args.trackio_space_id
    if space_id:
        if space_id != "trackio" and "/" not in space_id:
            logger.warning(
                f"trackio_space_id '{space_id}' should typically be in format "
                "'org/space' for Hugging Face Spaces deployment."
            )

    # --- Inform about default project usage ---
    if training_args.project == "huggingface":
        logger.info(
            "Using default project name 'huggingface'. "
            "Consider setting a custom project name with --project "
            "for better organization."
        )

    # --- Validate hub repo privacy flag ---
    if training_args.hub_private_repo:
        logger.info("Repository will be created as private on Hugging Face Hub.")

    # --- Recommend run_name for experiment clarity ---
    if not training_args.run_name:
        logger.warning("Consider setting --run_name for better experiment tracking clarity.")