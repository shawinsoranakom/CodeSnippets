def get_correct_attn_implementation(self, requested_attention: str | None, is_init_check: bool = False) -> str:
        applicable_attention = "sdpa" if requested_attention is None else requested_attention
        if applicable_attention not in ["eager"] + ALL_ATTENTION_FUNCTIONS.valid_keys():
            message = (
                f'Specified `attn_implementation="{applicable_attention}"` is not supported. The only possible arguments are '
                '`attn_implementation="eager"`, `"paged|eager"`'
            )
            # check `supports_flash_attn_2` for BC with custom code. TODO: remove after a few releases
            if self._supports_flash_attn or getattr(self, "_supports_flash_attn_2", False):
                message += ", "
                for fa_version in FLASH_ATTENTION_COMPATIBILITY_MATRIX.keys():
                    message += f'`"attn_implementation=flash_attention_{fa_version}"`, `"attn_implementation=paged|flash_attention_{fa_version}"`, '
                message = message[:-2]  # remove trailing comma
            if self._supports_sdpa:
                message += ', `"attn_implementation=sdpa"`, `"attn_implementation=paged|sdpa"`'
            if self._supports_flex_attn:
                message += ', `"attn_implementation=flex_attention"`'
            raise ValueError(message + ".")

        # Perform relevant checks
        if is_flash_attention_requested(requested_attention_implementation=applicable_attention) and (
            fa_matched := re.search(r"^flash_attention_(\d)$", applicable_attention)
        ):
            fa_version = int(fa_matched.group(1))  # last digit
            self._flash_attn_can_dispatch(flash_attn_version=fa_version, is_init_check=is_init_check)
        elif "flex_attention" in applicable_attention:
            self._flex_attn_can_dispatch(is_init_check)
        elif "sdpa" in applicable_attention:
            # Sdpa is the default, so we try it and fallback to eager otherwise when not possible
            try:
                self._sdpa_can_dispatch(is_init_check)
            except (ValueError, ImportError) as e:
                if requested_attention is not None and "sdpa" in requested_attention:
                    raise e
                applicable_attention = "eager"

        return applicable_attention