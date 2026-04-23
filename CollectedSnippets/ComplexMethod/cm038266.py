def _create_hf_to_vllm_mapper(self):
        """
        Create a WeightsMapper to map checkpoint weight names to module qualnames.

        This handles:

        - Transformers weight renaming:
            - from `WeightRenaming` in Transformers v5
            - from `_checkpoint_conversion_mapping` in Transformers v4
        - Checkpoints saved with a base model prefix that is not `model`
        - Checkpoints saved with no base model prefix
        - Any quantization config specific mappings
        """
        self.hf_to_vllm_mapper = WeightsMapper()
        orig_to_new_regex = self.hf_to_vllm_mapper.orig_to_new_regex

        if Version(transformers.__version__) >= Version("5.0.0"):
            from transformers.conversion_mapping import (
                WeightRenaming,
                get_model_conversion_mapping,
            )

            for mapping in get_model_conversion_mapping(self.model):
                # Handle weights which have been renamed in Transformers
                if isinstance(mapping, WeightRenaming):
                    # Recompile using regex (Transformers used re)
                    compiled_sources = re.compile(
                        mapping.compiled_sources.pattern, mapping.compiled_sources.flags
                    )
                    target_pattern = mapping.target_patterns[0]
                    orig_to_new_regex[compiled_sources] = target_pattern
                # TODO: Handle WeightConverter to enable layer merging
        else:
            # Replace legacy suffixes used for norms
            # TODO(hmellor): Remove this when Transformers v4 support is dropped
            orig_to_new_regex.update(
                {
                    re.compile(r"\.gamma$"): ".weight",
                    re.compile(r"\.beta$"): ".bias",
                }
            )

        # Handle weights which have been renamed in Transformers
        # TODO(hmellor): Remove this when Transformers v4 support is dropped
        ccm = getattr(self.model, "_checkpoint_conversion_mapping", {})
        for source, target in ccm.items():
            orig_to_new_regex[re.compile(source)] = target

        # Handle unexpected weights which should be ignored
        if self.model._keys_to_ignore_on_load_unexpected is not None:
            for key in self.model._keys_to_ignore_on_load_unexpected:
                orig_to_new_regex[re.compile(key)] = None

        # Standardise base model prefix
        bmp = self.model.base_model_prefix
        expected_bmp = r"model.\1"
        # Handle checkpoints saved with different base model prefix
        if bmp and bmp != "model":
            different_bmp_pattern = re.compile(rf"^{bmp}\.(.+)")
            orig_to_new_regex[different_bmp_pattern] = expected_bmp
        # Handle direct children of self.model which were saved without the model prefix
        direct_children = chain(
            self.model.named_children(),
            self.model.named_parameters(recurse=False),
            self.model.named_buffers(recurse=False),
        )
        model_children = "|".join(name for name, _ in direct_children)
        missing_bmp_pattern = re.compile(rf"^(?!model\.)(({model_children}).*)")
        orig_to_new_regex[missing_bmp_pattern] = expected_bmp
        # Handle weights saved as direct children of self.model which no longer are
        unexpected_bmp_pattern = re.compile(rf"^(model\.)((?!{model_children}).+)")
        orig_to_new_regex[unexpected_bmp_pattern] = r"\2"
        # Handle lm_head which was saved inside the base model
        nested_lm_head_pattern = re.compile(r"^model\.(.+\.)*(lm_head.+)")
        orig_to_new_regex[nested_lm_head_pattern] = r"\2"

        # Apply mapping to quantization config if needed
        self._maybe_apply_model_mapping()