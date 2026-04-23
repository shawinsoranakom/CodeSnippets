def override_quantization_method(
        cls, hf_quant_cfg, user_quant, hf_config=None
    ) -> "QuantizationMethods | None":
        # Skip override to marlin kernels, as they are not
        # batch invariant
        if envs.VLLM_BATCH_INVARIANT:
            return None

        can_convert = cls.is_awq_marlin_compatible(hf_quant_cfg)
        is_valid_user_quant = (
            user_quant is None or user_quant == "marlin" or user_quant == "awq_marlin"
        )

        if can_convert and is_valid_user_quant:
            msg = (
                "The model is convertible to {} during runtime."
                " Using {} kernel.".format(cls.get_name(), cls.get_name())
            )
            logger.info(msg)
            return cls.get_name()

        if can_convert and user_quant == "awq":
            logger.info(
                "Detected that the model can run with awq_marlin"
                ", however you specified quantization=awq explicitly,"
                " so forcing awq. Use quantization=awq_marlin for"
                " faster inference"
            )
        return None