def inspect_model_cls(
        self,
        architectures: str | list[str],
        model_config: ModelConfig,
    ) -> tuple[_ModelInfo, str]:
        if isinstance(architectures, str):
            architectures = [architectures]
        if not architectures:
            raise ValueError("No model architectures are specified")

        # Require transformers impl
        if model_config.model_impl == "transformers":
            arch = self._try_resolve_transformers(architectures[0], model_config)
            if arch is not None:
                model_info = self._try_inspect_model_cls(arch)
                if model_info is not None:
                    return (model_info, arch)
        elif model_config.model_impl == "terratorch":
            model_info = self._try_inspect_model_cls("Terratorch")
            return (model_info, "Terratorch")

        # Fallback to transformers impl (after resolving convert_type)
        if (
            all(arch not in self.models for arch in architectures)
            and model_config.model_impl == "auto"
            and getattr(model_config, "convert_type", "none") == "none"
        ):
            arch = self._try_resolve_transformers(architectures[0], model_config)
            if arch is not None:
                model_info = self._try_inspect_model_cls(arch)
                if model_info is not None:
                    return (model_info, arch)

        for arch in architectures:
            normalized_arch = self._normalize_arch(arch, model_config)
            model_info = self._try_inspect_model_cls(normalized_arch)
            if model_info is not None:
                return (model_info, arch)

        # Fallback to transformers impl (before resolving runner_type)
        if (
            all(arch not in self.models for arch in architectures)
            and model_config.model_impl == "auto"
        ):
            arch = self._try_resolve_transformers(architectures[0], model_config)
            if arch is not None:
                model_info = self._try_inspect_model_cls(arch)
                if model_info is not None:
                    return (model_info, arch)

        return self._raise_for_unsupported(architectures)