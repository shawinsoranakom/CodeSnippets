def _verify_model_compatibility(
        self, model: nn.Module, model_config: ModelConfig
    ) -> None:
        """
        Verify that the model is compatible with BitsAndBytes quantization.
        """
        if not hasattr(model, "load_weights"):
            raise AttributeError(
                "The required method 'load_weights' is not defined in class"
                f" {type(model).__name__}."
            )

        if not hasattr(model, "packed_modules_mapping"):
            raise AttributeError(
                f"Model {type(model).__name__} does not support BitsAndBytes "
                "quantization yet. No 'packed_modules_mapping' found."
            )

        quant_config = getattr(model_config.hf_config, "quantization_config", None)
        if quant_config and (quant_method := quant_config.get("quant_method")):
            if quant_method == "bitsandbytes":
                self.pre_quant = True
            else:
                raise ValueError(
                    f"BitsAndBytes loader does not support {quant_method} quantization"
                )

        # The quant_states in pre_quantized models cannot work with a split
        # weight tensor. So TP does not work with pre_quantized bnb models.
        if self.pre_quant and get_tensor_model_parallel_world_size() > 1:
            raise ValueError(
                "Prequant BitsAndBytes models with tensor parallelism is not "
                "supported. Please try with pipeline parallelism."
            )
        if quant_config and self.pre_quant:
            self.load_8bit = quant_config.get("load_in_8bit", False)