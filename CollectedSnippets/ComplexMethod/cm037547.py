def extract_reasoning_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],
        current_token_ids: Sequence[int],
        delta_token_ids: Sequence[int],
    ) -> DeltaMessage | None:
        """Extract streaming reasoning, stripping ``thought\\n`` from the
        first reasoning delta(s).

        The ``thought\\n`` prefix may arrive as a single delta or split
        across multiple deltas (e.g. ``"thought"`` then ``"\\n"``). We
        buffer early reasoning tokens until we can determine whether the
        prefix is present, then emit the buffered content minus the
        prefix.

        Unlike the previous implementation which reconstructed accumulated
        reasoning from ``current_text``, this uses instance state
        (``_reasoning_text``) to track only the reasoning content returned
        by the base parser. This is necessary because
        ``skip_special_tokens=True`` (the vLLM default) causes the
        ``<|channel>`` delimiter to be invisible in ``current_text``,
        making it impossible to separate pre-reasoning content from
        reasoning content via string matching.
        """
        result = super().extract_reasoning_streaming(
            previous_text,
            current_text,
            delta_text,
            previous_token_ids,
            current_token_ids,
            delta_token_ids,
        )
        if result is None:
            return None

        if result.reasoning is None:
            return result

        # Accumulate ONLY the reasoning text from base parser results.
        # This is immune to pre-reasoning content pollution.
        self._reasoning_text += result.reasoning

        # Once the prefix has been handled, all subsequent reasoning
        # deltas pass through unchanged.
        if self._prefix_stripped:
            return result

        # ---- Prefix stripping logic ----

        # Case 1: We've accumulated enough to confirm the prefix is
        # present. Strip it and pass through the remainder.
        if self._reasoning_text.startswith(_THOUGHT_PREFIX):
            prefix_len = len(_THOUGHT_PREFIX)
            # How much reasoning was accumulated before this delta?
            prev_reasoning_len = len(self._reasoning_text) - len(result.reasoning)
            if prev_reasoning_len >= prefix_len:
                # Prefix was already consumed by prior deltas; this
                # delta is entirely real content — pass through.
                self._prefix_stripped = True
                return result
            else:
                # Part or all of the prefix is in this delta.
                chars_of_prefix_in_delta = prefix_len - prev_reasoning_len
                stripped = result.reasoning[chars_of_prefix_in_delta:]
                if stripped:
                    self._prefix_stripped = True
                    result.reasoning = stripped
                    return result
                else:
                    if len(self._reasoning_text) >= prefix_len:
                        self._prefix_stripped = True
                        result.reasoning = ""
                        return result
                    return None

        # Case 2: Accumulated text is a strict prefix of
        # _THOUGHT_PREFIX (e.g. we've only seen "thou" so far).
        # Buffer by suppressing — we can't yet tell if this will
        # become the full prefix or diverge.
        if _THOUGHT_PREFIX.startswith(self._reasoning_text):
            return None

        # Case 3: Accumulated text doesn't match the thought prefix
        # at all. This means prior deltas were buffered (suppressed
        # by Case 2) but the text diverged. Re-emit the full
        # accumulated text to avoid data loss.
        self._prefix_stripped = True
        result.reasoning = self._reasoning_text
        return result