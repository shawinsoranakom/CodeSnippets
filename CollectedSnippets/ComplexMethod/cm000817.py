def _should_strip_thinking_block(
    block: object,
    *,
    is_last_turn: bool,
    producing_model: str | None = None,
) -> bool:
    """Return True when *block* is a thinking block that should be removed
    from a transcript entry before upload.

    Strip only when the block CAN'T be replayed safely.  Never strip a
    valid Anthropic-issued thinking block — it carries real reasoning
    state that preserves context continuity on ``--resume``.

    Strip rules (first match wins):

    1. **Non-Anthropic producer (any position)** — thinking blocks from
       Kimi / DeepSeek / GPT-OSS via OpenRouter's Anthropic-compat shim
       carry either no signature or a placeholder string that passes a
       non-empty check but fails Anthropic's cryptographic validation.
       Strip unconditionally; they also add low-value tokens to the
       replay context.
    2. **Malformed ``thinking`` (any position, Anthropic producer,
       empty signature)** — shouldn't happen in practice, but if the
       signature is missing / empty the block can't be validated.
       Safer to drop than to 400 the next turn.
    3. **Stale non-last entry with unknown producer** — when the
       caller doesn't wire ``producing_model`` through (legacy paths /
       older tests) we can't tell if the block is safe to keep; fall
       back to the old behaviour of dropping non-last thinking blocks
       to avoid replaying an unverifiable block to Anthropic.

    Preserved:

    * Anthropic ``thinking`` with non-empty signature — at any
      position, last OR non-last.  Keeping prior-turn reasoning
      chains helps continuity on multi-round SDK resumes without any
      risk of signature rejection.
    * Anthropic ``redacted_thinking`` — carries an encrypted ``data``
      payload instead of a ``signature``; by design signature-less,
      but Anthropic-issued and safely replayable.
    """
    if not isinstance(block, dict):
        return False
    btype = block.get("type")
    if btype not in _THINKING_BLOCK_TYPES:
        return False
    # Legacy call sites pass producing_model=None — preserve the old
    # "strip-all-non-last-thinking" heuristic for those so we don't
    # regress callers that haven't been updated.
    if producing_model is None:
        if not is_last_turn:
            return True
        if btype != "thinking":
            return False
        signature = block.get("signature")
        return not (isinstance(signature, str) and signature)
    # Non-Anthropic producer — strip at any position.  These blocks
    # CAN'T be cryptographically validated by Anthropic on replay.
    if not _is_anthropic_model(producing_model):
        return True
    # Anthropic producer, redacted_thinking: always preserve — the
    # ``data`` field is the signature analog.
    if btype == "redacted_thinking":
        return False
    # Anthropic producer, ``thinking``: keep iff it has a real
    # (non-empty) signature.  Empty-signature Anthropic thinking
    # shouldn't happen but guard against it anyway.
    signature = block.get("signature")
    return not (isinstance(signature, str) and signature)