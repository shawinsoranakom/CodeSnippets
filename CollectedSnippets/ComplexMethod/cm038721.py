def _get_default_convert_type(
        self,
        architectures: list[str],
        runner_type: RunnerType,
    ) -> ConvertType:
        registry = self.registry

        for arch in architectures:
            if arch in registry.get_supported_archs():
                if runner_type == "generate" and registry.is_text_generation_model(
                    architectures, self
                ):
                    return "none"
                if runner_type == "pooling" and registry.is_pooling_model(
                    architectures, self
                ):
                    return "none"

            match = try_match_architecture_defaults(arch, runner_type=runner_type)
            if match:
                _, (_, convert_type) = match
                return convert_type

        # This is to handle Sentence Transformers models that use *ForCausalLM
        # and also multi-modal pooling models which are not defined as
        # Sentence Transformers models
        if runner_type == "pooling":
            return "embed"

        return "none"