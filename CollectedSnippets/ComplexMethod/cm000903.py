async def _resolve_sdk_model_for_request(
    model: "CopilotLlmModel | None",
    session_id: str,
    user_id: str | None = None,
) -> str | None:
    """Resolve the SDK model string for a turn.

    Priority (highest first):
    1. ``config.claude_agent_model`` — unconditional override, bypasses LD.
    2. LaunchDarkly ``copilot-thinking-{tier}-model`` if it serves a value
       different from the config default for *user_id*.  An LD-served
       override wins over subscription mode so admins can route specific
       users to a specific model without flipping subscription on/off.
    3. ``config.use_claude_code_subscription`` on the standard tier —
       returns ``None`` so the CLI picks the subscription default (this
       branch fires when LD has no opinion, i.e. the value equals the
       config default).
    4. ``ChatConfig`` static default for the tier.
    """
    if config.claude_agent_model:
        return config.claude_agent_model

    tier_name: "CopilotLlmModel" = "advanced" if model == "advanced" else "standard"
    # Strip at read time so a stray trailing space in ``CHAT_*_MODEL`` (a
    # common ``.env`` pitfall) doesn't make the ``resolved == tier_default``
    # comparison below spuriously diverge — ``resolve_model`` already strips
    # the LD side, so both halves must end up whitespace-normalised to stay
    # equal when they're semantically equal.  Downstream ``_normalize_model_name``
    # also benefits from the strip.
    tier_default = (
        config.thinking_advanced_model
        if tier_name == "advanced"
        else config.thinking_standard_model
    ).strip()

    resolved = await _resolve_thinking_model_for_user(tier_name, user_id)

    # Subscription mode on standard tier only wins when LD has no opinion
    # (value == config default ⇒ admin hasn't explicitly pointed this
    # user somewhere).  Any LD override — even to the same value with
    # stripped whitespace normalised — is an explicit admin choice that
    # must be honoured.  Without this, a subscription-mode deployment
    # silently ignores the ``copilot-thinking-standard-model`` flag
    # entirely, which defeats the point of cohort-based routing.
    ld_overrides_default = resolved != tier_default
    if (
        not ld_overrides_default
        and tier_name == "standard"
        and config.use_claude_code_subscription
    ):
        logger.info(
            "[SDK] [%s] Subscription default (tier=standard, LD unset)",
            session_id[:12] if session_id else "?",
        )
        return None
    try:
        sdk_model = _normalize_model_name(resolved)
    except ValueError as exc:
        # The per-user LD value didn't pass ``_normalize_model_name``'s
        # vendor check (most commonly: a ``moonshotai/kimi-*`` slug on a
        # direct-Anthropic deployment that has no OpenRouter route).  Fail
        # soft to the TIER-SPECIFIC config default — using the generic
        # ``_resolve_sdk_model()`` here would pin advanced-tier requests to
        # ``thinking_standard_model`` (Sonnet) whenever LD misconfigures
        # the advanced cell, silently downgrading the user's chosen tier.
        try:
            sdk_model = _normalize_model_name(tier_default)
        except ValueError:
            # Config default is *also* invalid for the active routing
            # mode — this is a deployment-level misconfig that the
            # ``model_validator`` should catch at startup.  Re-raise the
            # original LD error so the issue surfaces loudly rather than
            # returning something misleading.
            raise exc
        logger.warning(
            "[SDK] [%s] LD model %r rejected for tier=%s (%s); falling "
            "back to tier default %s",
            session_id[:12] if session_id else "?",
            resolved,
            tier_name,
            exc,
            sdk_model,
        )
        return sdk_model
    logger.info(
        "[SDK] [%s] Resolved model for tier=%s: %s",
        session_id[:12] if session_id else "?",
        tier_name,
        sdk_model,
    )
    return sdk_model