def _init_model(self) -> HFModel:
        """Init model.

        Transformers can choose the proper model init context.
        https://github.com/huggingface/transformers/blob/v5.0.0rc0/src/transformers/modeling_utils.py#L3538
        """
        if self.args.init_config is not None:
            from ..plugins.model_plugins.initialization import InitPlugin

            init_device = InitPlugin(self.args.init_config.name)()
        else:
            init_device = DistributedInterface().current_device

        init_kwargs = {} if self._deepspeed_zero3_enabled else {"device_map": init_device}

        if self.args.quant_config is not None:
            from ..plugins.model_plugins.quantization import QuantizationPlugin

            init_kwargs = QuantizationPlugin(self.args.quant_config.name)(
                init_kwargs=init_kwargs,
                config=self.model_config,
                tokenizer=self.processor,
                model_args=self.args,
                is_trainable=self.is_train,
            )

        if self.args.model_class == ModelClass.LLM:
            from transformers import AutoModelForCausalLM, AutoModelForImageTextToText

            if type(self.model_config) in AutoModelForImageTextToText._model_mapping.keys():
                AutoClass = AutoModelForImageTextToText
            else:
                AutoClass = AutoModelForCausalLM

        elif self.args.model_class == ModelClass.CLS:
            from transformers import AutoModelForTokenClassification

            AutoClass = AutoModelForTokenClassification
        else:
            from transformers import AutoModel

            AutoClass = AutoModel

        if init_device.type == DeviceType.META:
            assert self.args.quant_config is None, "Quantization is not supported with meta device."
            with init_empty_weights():
                model = AutoClass.from_config(self.model_config)
        else:
            model = AutoClass.from_pretrained(
                self.args.model,
                config=self.model_config,
                dtype="auto",
                trust_remote_code=self.args.trust_remote_code,
                **init_kwargs,
            )

        init_mode = self.args.init_config.name if self.args.init_config is not None else "init_on_default"
        model._init_mode = init_mode

        if self.args.peft_config is None:
            if self.is_train:
                logger.info_rank0("Fine-tuning mode: full tuning")
                model = model.to(torch.float32)
            else:
                logger.info_rank0("Inference the original model")
        else:
            if self.args.peft_config.name == "lora" and init_mode == "init_on_meta":
                raise ValueError("Currently lora stage does not support loading model by meta.")

            from ..plugins.model_plugins.peft import PeftPlugin

            model = PeftPlugin(self.args.peft_config.name)(model, self.args.peft_config, self.is_train)

        if self.args.kernel_config is not None:
            from ..plugins.model_plugins.kernels.interface import KernelPlugin

            model = KernelPlugin(self.args.kernel_config.name)(
                model, include_kernels=self.args.kernel_config.get("include_kernels")
            )

        return model