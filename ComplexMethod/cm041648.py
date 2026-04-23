def apply(cls, **kwargs) -> HFModel:
        """Applies the NPU fused MoE kernel to the model.

        Args:
            **kwargs: Keyword arguments containing the model.

        Returns:
            HFModel: The model with patched MoE forward functions.

        Raises:
            ValueError: If the model is not provided.
            RuntimeError: If dependencies are not met.
        """
        model = kwargs.get("model", None)
        if model is None:
            raise ValueError(f"HFModel instance is required for {cls.__name__}.")

        if not cls.check_deps():
            raise RuntimeError("torch_npu is not available but NpuMoEFusedMoEKernel was called.")

        archs = getattr(model.config, "architectures", None) or []
        target_moe_mapping = None
        for arch in archs:
            if arch in kernel_moe_mapping:
                target_moe_mapping = kernel_moe_mapping[arch]
                break

        if target_moe_mapping is None:
            return model

        for module in model.modules():
            class_name = module.__class__.__name__
            if class_name in target_moe_mapping:
                new_forward_func = target_moe_mapping[class_name]
                module.forward = types.MethodType(new_forward_func, module)

        return model