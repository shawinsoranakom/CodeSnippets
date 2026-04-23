def apply(cls, **kwargs) -> "HFModel":
        """Apply RoPE acceleration by monkey-patching `apply_rotary_pos_emb`.

        This function iterates through the model's modules to find attention layers,
        identifies the module where they are defined, and replaces the original
        `apply_rotary_pos_emb` function in that module's namespace with the
        NPU-accelerated version from this file.

        Args:
            **kwargs: Keyword arguments containing the model.

        Returns:
            HFModel: The model with patched RoPE functions.

        Raises:
            RuntimeError: If dependencies are not met.
            ValueError: If the model is not provided.
        """
        if not cls.check_deps():
            raise RuntimeError(f"torch_npu is not available but {cls.__name__} was called.")

        model = kwargs.get("model", None)
        if model is None:
            raise ValueError(f"HFModel instance is required for {cls.__name__}.")

        _modules = set()
        for module in model.modules():
            if "Attention" in module.__class__.__name__:
                module_name = module.__class__.__module__
                if module_name in _modules:
                    continue
                try:
                    target_module = sys.modules[module_name]
                    if hasattr(target_module, "apply_rotary_pos_emb"):
                        if getattr(target_module, "apply_rotary_pos_emb") is not _apply_rotary_pos_emb:
                            setattr(target_module, "apply_rotary_pos_emb", _apply_rotary_pos_emb)
                            _modules.add(module_name)
                    if hasattr(target_module, "apply_multimodal_rotary_pos_emb"):
                        if (
                            getattr(target_module, "apply_multimodal_rotary_pos_emb")
                            is not _apply_multimodal_rotary_pos_emb_qwen25_vl
                        ):
                            setattr(
                                target_module,
                                "apply_multimodal_rotary_pos_emb",
                                _apply_multimodal_rotary_pos_emb_qwen25_vl,
                            )
                            _modules.add(module_name)
                except Exception as e:
                    logger.warning_rank0_once(f"Failed to apply RoPE kernel to module {module_name}: {e}")

        return model