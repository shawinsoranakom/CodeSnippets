def _process_model_before_weight_loading(self, model: "PreTrainedModel", checkpoint_files=None, **kwargs):
        self.modules_to_not_convert = self.get_modules_to_not_convert(
            model, self.quantization_config.modules_to_not_convert, model._keep_in_fp32_modules
        )
        if self.quantization_config.include_input_output_embeddings:
            input_emb = model.get_input_embeddings()
            input_emb_names = [name for name, module in model.named_modules() if id(module) == id(input_emb)]
            output_emb = model.get_output_embeddings()
            output_emb_names = [name for name, module in model.named_modules() if id(module) == id(output_emb)]
            self.modules_to_not_convert = [
                x for x in self.modules_to_not_convert if x not in input_emb_names + output_emb_names
            ]
        if checkpoint_files is not None:
            # Torchao needs access to all metadata later
            self.set_metadata(checkpoint_files)