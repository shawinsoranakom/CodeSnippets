def _adjust_missing_and_unexpected_keys(self, loading_info: LoadStateDictInfo) -> None:
        """Adjust the `missing_keys` and `unexpected_keys` based on current model's exception rules, to avoid
        raising unneeded warnings/errors. This is performed in-place.
        """
        # Old checkpoints may have keys for rotary_emb.inv_freq for each layer, however we moved this buffer to the main model
        # (so the buffer name has changed). Remove them in such a case. This is another exception that was not added to
        # `_keys_to_ignore_on_load_unexpected` as it touches many models -> we add it manually to the existing patterns
        has_inv_freq_buffers = any(buffer.endswith("rotary_emb.inv_freq") for buffer, _ in self.named_buffers())
        additional_unexpected_patterns = [r"rotary_emb\.inv_freq"] if has_inv_freq_buffers else []
        # Same idea for `position_ids`: used to be a persistent buffer, now `persistent=False` in most models.
        has_position_ids_buffers = any(buffer.endswith("position_ids") for buffer, _ in self.named_buffers())
        if has_position_ids_buffers:
            additional_unexpected_patterns.append(r"(^|\.)position_ids$")

        missing_patterns = self._keys_to_ignore_on_load_missing or []
        unexpected_patterns = (self._keys_to_ignore_on_load_unexpected or []) + additional_unexpected_patterns
        ignore_missing_regex, ignore_unexpected_regex = None, None
        if len(missing_patterns) > 0:
            ignore_missing_regex = re.compile("|".join(rf"({pattern})" for pattern in missing_patterns))
        if len(unexpected_patterns) > 0:
            ignore_unexpected_regex = re.compile("|".join(rf"({pattern})" for pattern in unexpected_patterns))

        # Clean-up missing keys
        if ignore_missing_regex is not None:
            loading_info.missing_keys = {
                key for key in loading_info.missing_keys if ignore_missing_regex.search(key) is None
            }

        # Clean-up unexpected keys
        if ignore_unexpected_regex is not None:
            loading_info.unexpected_keys = {
                key for key in loading_info.unexpected_keys if ignore_unexpected_regex.search(key) is None
            }