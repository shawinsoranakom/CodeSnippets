async def extract_business_understanding(
    formatted_text: str,
) -> BusinessUnderstandingInput:
    """Use an LLM to extract structured business understanding from form text.

    Raises on timeout or unparseable response so the caller can handle it.
    """
    settings = Settings()
    api_key = settings.secrets.open_router_api_key
    client = AsyncOpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)

    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": f"{_EXTRACTION_PROMPT}{formatted_text}{_EXTRACTION_SUFFIX}",
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            ),
            timeout=_LLM_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("Tally: LLM extraction timed out")
        raise

    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Tally: LLM returned invalid JSON, skipping extraction")
        raise

    # Filter out null values before constructing
    cleaned = {k: v for k, v in data.items() if v is not None}

    # Validate suggested_prompts: themed dict, filter >20 words, cap at 5 per theme
    raw_prompts = cleaned.get("suggested_prompts", {})
    if isinstance(raw_prompts, dict):
        themed: dict[str, list[str]] = {}
        for theme in SUGGESTION_THEMES:
            theme_prompts = raw_prompts.get(theme, [])
            if not isinstance(theme_prompts, list):
                continue
            valid = [
                s
                for p in theme_prompts
                if isinstance(p, str) and (s := p.strip()) and len(s.split()) <= 20
            ]
            if valid:
                themed[theme] = valid[:PROMPTS_PER_THEME]
        if themed:
            cleaned["suggested_prompts"] = themed
        else:
            cleaned.pop("suggested_prompts", None)
    else:
        cleaned.pop("suggested_prompts", None)

    return BusinessUnderstandingInput(**cleaned)