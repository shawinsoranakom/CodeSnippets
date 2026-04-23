def _check_and_adjust_attn_implementation(
        self, attn_implementation: str | None, is_init_check: bool = False, allow_all_kernels: bool = False
    ) -> str:
        """
        Check that the `attn_implementation` exists and is supported by the models, and try to get the kernel from hub if
        it matches hf kernels pattern.

        Args:
            attn_implementation (`str` or `None`):
                The attention implementation to check for existence/validity.
            is_init_check (`bool`, *optional*):
                Whether this check is performed early, i.e. at __init__ time, or later when the model and its weights are
                fully instantiated. This is needed as we also check the devices of the weights, which are only available
                later after __init__. This allows to raise proper exceptions early before instantiating the full models
                if we know that the model does not support the requested attention.
            allow_all_kernels (`bool`, optional):
                Whether to load kernels from unverified hub repos, if `attn_implementation` is a custom kernel outside
                of the `kernels-community` hub repository.

        Returns:
            `str`: The final attention implementation to use, including potential fallbacks from sdpa to eager, or from
            None to sdpa (to potentially eager).
        """
        # Auto-correct model's default flash implementation if specified
        if attn_implementation is not None:
            is_paged = attn_implementation.startswith("paged|")
            base_implementation = attn_implementation.removeprefix("paged|")

            compatible_flash_implementations = getattr(self, "_compatible_flash_implementations", None)
            if (
                is_flash_attention_requested(requested_attention_implementation=base_implementation)
                and compatible_flash_implementations is not None
                and base_implementation not in compatible_flash_implementations
            ):
                default_flash_implementation = (
                    f"paged|{compatible_flash_implementations[0]}" if is_paged else compatible_flash_implementations[0]
                )

                logger.warning_once(
                    f"This model is compatible with the following flash attention implementations: `{compatible_flash_implementations}`. "
                    f"Automatically falling back to `{default_flash_implementation}` instead of `{attn_implementation}`."
                )
                attn_implementation = default_flash_implementation

        applicable_attn_implementation = attn_implementation
        is_paged = attn_implementation is not None and attn_implementation.startswith("paged|")

        requested_original_flash_attn = False
        if is_flash_attention_requested(requested_attention_implementation=attn_implementation):
            # If FA not installed, do not fail but use kernels instead if possible
            for fa_version in FLASH_ATTENTION_COMPATIBILITY_MATRIX.keys():
                # Check whether we have an original FA requested but not available in the env
                if requested_original_flash_attn := (
                    attn_implementation.removeprefix("paged|") == f"flash_attention_{fa_version}"
                    and not FLASH_ATTENTION_COMPATIBILITY_MATRIX[fa_version]["general_availability_check"]()
                ):
                    break

        if (
            self._supports_flash_attn
            and requested_original_flash_attn
            and is_kernels_available()
            and not is_torch_npu_available()
        ):
            applicable_attn_implementation = FLASH_ATTN_KERNEL_FALLBACK[attn_implementation.removeprefix("paged|")]

            if is_torch_xpu_available() and attn_implementation.removeprefix("paged|") == "flash_attention_2":
                # On XPU, kernels library is the native implementation
                # Disabling this flag to avoid giving wrong fallbacks on errors and warnings
                requested_original_flash_attn = False

            if is_paged:
                applicable_attn_implementation = f"paged|{applicable_attn_implementation}"

        if is_kernel(applicable_attn_implementation):
            try:
                # preload flash attention here to allow compile with fullgraph
                if is_paged:
                    lazy_import_paged_flash_attention(
                        applicable_attn_implementation, allow_all_kernels=allow_all_kernels
                    )
                else:
                    lazy_import_flash_attention(applicable_attn_implementation, allow_all_kernels=allow_all_kernels)

                # log that we used kernel fallback if successful
                if requested_original_flash_attn:
                    logger.warning_once(
                        f"You do not have `flash_attn` installed, using `{applicable_attn_implementation}` "
                        "from the `kernels` library instead!"
                    )
            except Exception as e:
                # raise the proper exception for requested flash attention
                if requested_original_flash_attn:
                    fa_version = int(attn_implementation[-1])  # "flash_attention_(2|3|...)"
                    self._flash_attn_can_dispatch(flash_attn_version=fa_version, is_init_check=is_init_check)

                # error properly out if a kernel was specifically requested
                raise e
        else:
            applicable_attn_implementation = self.get_correct_attn_implementation(
                applicable_attn_implementation, is_init_check
            )

            # preload flash attention here to allow compile with fullgraph
            if is_flash_attention_requested(requested_attention_implementation=applicable_attn_implementation):
                lazy_import_flash_attention(applicable_attn_implementation)

        return applicable_attn_implementation