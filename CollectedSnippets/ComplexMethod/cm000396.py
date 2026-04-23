async def _call_llm_for_simulation(
    system_prompt: str,
    user_prompt: str,
    *,
    label: str = "simulate",
    user_id: str | None = None,
) -> dict[str, Any]:
    """Send a simulation prompt to the LLM and return the parsed JSON dict.

    Handles client acquisition, retries on invalid JSON, logging, and platform
    cost tracking.  The dry-run simulator calls OpenRouter on the platform's
    key rather than a user's own API credentials, so every successful call is
    recorded against the triggering ``user_id``'s rate-limit counter via
    ``persist_and_record_usage`` (same rails as every copilot turn).

    Raises:
        RuntimeError: If no LLM client is available.
        ValueError: If all retry attempts are exhausted.
    """
    client = get_openai_client(prefer_openrouter=True)
    if client is None:
        raise RuntimeError(
            "[SIMULATOR ERROR — NOT A BLOCK FAILURE] No LLM client available "
            "(missing OpenAI/OpenRouter API key)."
        )

    model = _simulator_model()
    last_error: Exception | None = None
    for attempt in range(_MAX_JSON_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=model,
                temperature=_TEMPERATURE,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                extra_body=_OPENROUTER_INCLUDE_USAGE_COST,
            )
            if not response.choices:
                raise ValueError("LLM returned empty choices array")
            raw = response.choices[0].message.content or ""
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError(f"LLM returned non-object JSON: {raw[:200]}")

            usage = response.usage
            if usage is not None:
                logger.debug(
                    "simulate(%s): attempt=%d tokens=%d/%d",
                    label,
                    attempt + 1,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                )
            else:
                logger.debug(
                    "simulate(%s): attempt=%d usage unavailable", label, attempt + 1
                )

            await _track_simulator_cost(usage=usage, user_id=user_id, model=model)
            return parsed

        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            logger.warning(
                "simulate(%s): JSON parse error on attempt %d/%d: %s",
                label,
                attempt + 1,
                _MAX_JSON_RETRIES,
                e,
            )
        except Exception as e:
            last_error = e
            logger.error("simulate(%s): LLM call failed: %s", label, e, exc_info=True)
            break

    msg = (
        f"[SIMULATOR ERROR — NOT A BLOCK FAILURE] Failed after {_MAX_JSON_RETRIES} "
        f"attempts: {last_error}"
    )
    logger.error(
        "simulate(%s): all retries exhausted; last_error=%s", label, last_error
    )
    raise ValueError(msg)