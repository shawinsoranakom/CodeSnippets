def resolve_tracking(
    provider: str,
    stats: NodeExecutionStats,
    input_data: dict[str, Any],
) -> tuple[str, float]:
    """Return (tracking_type, tracking_amount) based on provider billing model.

    Preference order:
    1. Block-declared: if the block set `provider_cost_type` on its stats,
       honor it directly (paired with `provider_cost` as the amount).
    2. Heuristic fallback: infer from `provider_cost`/token counts, then
       from provider name for per-character / per-second billing.
    """
    # 1. Block explicitly declared its cost type (only when an amount is present)
    if stats.provider_cost_type and stats.provider_cost is not None:
        return stats.provider_cost_type, max(0.0, stats.provider_cost)

    # 2. Provider returned actual USD cost (OpenRouter, Exa)
    if stats.provider_cost is not None:
        return "cost_usd", max(0.0, stats.provider_cost)

    # 3. LLM providers: track by tokens
    if stats.input_token_count or stats.output_token_count:
        return "tokens", float(
            (stats.input_token_count or 0) + (stats.output_token_count or 0)
        )

    # 4. Provider-specific billing heuristics

    # TTS: billed per character of input text
    if provider == ProviderName.UNREAL_SPEECH.value:
        text = input_data.get("text", "")
        return "characters", float(len(text)) if isinstance(text, str) else 0.0

    # D-ID + ElevenLabs voice: billed per character of script
    if provider in _CHARACTER_BILLED_PROVIDERS:
        text = (
            input_data.get("script_input", "")
            or input_data.get("text", "")
            or input_data.get("script", "")  # VideoNarrationBlock uses `script`
        )
        return "characters", float(len(text)) if isinstance(text, str) else 0.0

    # E2B: billed per second of sandbox time
    if provider == ProviderName.E2B.value:
        return "sandbox_seconds", round(stats.walltime, 3) if stats.walltime else 0.0

    # Video/image gen: walltime includes queue + generation + polling
    if provider in _WALLTIME_BILLED_PROVIDERS:
        return "walltime_seconds", round(stats.walltime, 3) if stats.walltime else 0.0

    # Per-request: Google Maps, Ideogram, Nvidia, Apollo, etc.
    # All billed per API call - count 1 per block execution.
    return "per_run", 1.0