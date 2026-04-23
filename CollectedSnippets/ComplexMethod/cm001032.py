async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        query: str = "",
        max_results: int = _DEFAULT_MAX_RESULTS,
        deep: bool = False,
        **kwargs: Any,
    ) -> ToolResponseBase:
        query = (query or "").strip()
        session_id = session.session_id if session else None
        if not query:
            return ErrorResponse(
                message="Please provide a non-empty search query.",
                error="missing_query",
                session_id=session_id,
            )

        try:
            max_results = int(max_results)
        except (TypeError, ValueError):
            max_results = _DEFAULT_MAX_RESULTS
        max_results = max(1, min(max_results, _HARD_MAX_RESULTS))

        if not _chat_config.api_key or not _chat_config.base_url:
            return ErrorResponse(
                message=(
                    "Web search is unavailable — the deployment has no "
                    "OpenRouter credentials configured."
                ),
                error="web_search_not_configured",
                session_id=session_id,
            )

        client = AsyncOpenAI(
            api_key=_chat_config.api_key, base_url=_chat_config.base_url
        )
        model_used = _DEEP_MODEL if deep else _QUICK_MODEL
        max_tokens = _DEEP_MAX_TOKENS if deep else _QUICK_MAX_TOKENS

        try:
            resp = await client.chat.completions.create(
                model=model_used,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": query}],
                extra_body=_OPENROUTER_INCLUDE_USAGE_COST,
            )
        except Exception as exc:
            logger.warning(
                "[web_search] OpenRouter call failed (deep=%s) for query=%r: %s",
                deep,
                query,
                exc,
            )
            return ErrorResponse(
                message=f"Web search failed: {exc}",
                error="web_search_failed",
                session_id=session_id,
            )

        answer = _extract_answer(resp)
        results = _extract_results(resp, limit=max_results)
        cost_usd = _extract_cost_usd(resp.usage)

        try:
            await persist_and_record_usage(
                session=session,
                user_id=user_id,
                prompt_tokens=resp.usage.prompt_tokens if resp.usage else 0,
                completion_tokens=resp.usage.completion_tokens if resp.usage else 0,
                log_prefix="[web_search]",
                cost_usd=cost_usd,
                model=model_used,
                provider="open_router",
            )
        except Exception as exc:
            logger.warning("[web_search] usage tracking failed: %s", exc)

        return WebSearchResponse(
            message=f"Found {len(results)} result(s) for {query!r}.",
            query=query,
            answer=answer,
            results=results,
            search_requests=1 if results else 0,
            session_id=session_id,
        )