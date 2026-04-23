async def populate_understanding_from_tally(user_id: str, email: str) -> None:
    """Main orchestrator: check Tally for a matching submission and populate understanding.

    Fire-and-forget safe — all exceptions are caught and logged.
    """
    try:
        # Check if understanding already exists (idempotency)
        existing = await get_business_understanding(user_id)
        if existing is not None:
            logger.debug(
                f"Tally: user {user_id} already has business understanding, skipping"
            )
            return

        # Check required config is present
        settings = Settings()
        if not settings.secrets.tally_api_key or not settings.secrets.tally_form_id:
            logger.debug("Tally: Tally config incomplete, skipping")
            return
        if not settings.secrets.open_router_api_key:
            logger.debug("Tally: no OpenRouter API key configured, skipping")
            return

        # Look up submission by email
        masked = _mask_email(email)
        result = await find_submission_by_email(settings.secrets.tally_form_id, email)
        if result is None:
            logger.debug(f"Tally: no submission found for {masked}")
            return

        submission, questions = result
        logger.info(f"Tally: found submission for {masked}, extracting understanding")

        # Format and extract
        formatted = format_submission_for_llm(submission, questions)
        if not formatted.strip():
            logger.warning("Tally: formatted submission was empty, skipping")
            return

        understanding_input = await extract_business_understanding(formatted)

        # Upsert into database
        await upsert_business_understanding(user_id, understanding_input)
        logger.info(f"Tally: successfully populated understanding for user {user_id}")

    except Exception:
        logger.exception(f"Tally: error populating understanding for user {user_id}")