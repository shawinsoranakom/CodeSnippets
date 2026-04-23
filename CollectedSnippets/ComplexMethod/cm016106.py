def cast_based_on_args(self, model, example_inputs):
        if self.args.float32 or self.args.only in self.fp32_only_models:
            if not self.args.float32:
                log.warning("Model %s supports float32 only", self.args.only)
            model, example_inputs = cast_to_fp32(model, example_inputs)
        elif self.args.float16:
            if self.args.only in self.force_amp_for_fp16_bf16_models:
                log.warning(
                    "Model %s does not support float16, running with amp instead",
                    self.args.only,
                )
                self.args.amp = True
                self.setup_amp()
            else:
                model, example_inputs = cast_to_fp16(model, example_inputs)
        elif self.args.bfloat16:
            if self.args.only in self.force_amp_for_fp16_bf16_models:
                log.warning(
                    "Model %s does not support bfloat16, running with amp instead",
                    self.args.only,
                )
                self.args.amp = True
                self.setup_amp()
            elif self.args.only in self.force_fp16_for_bf16_models:
                log.warning(
                    "Model %s does not support bfloat16, running with float16 instead",
                    self.args.only,
                )
                model, example_inputs = cast_to_fp16(model, example_inputs)
            else:
                model, example_inputs = cast_to_bf16(model, example_inputs)

        return model, example_inputs