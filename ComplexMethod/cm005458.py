def export(
        self,
        input_ids: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        cache_position: torch.Tensor | None = None,
        dynamic_shapes: dict | None = None,
        strict: bool | None = None,
    ) -> torch.export.ExportedProgram:
        """
        Export the wrapped module using `torch.export`.

        Args:
            input_ids (`Optional[torch.Tensor]`):
                Tensor representing current input token id to the module. Must specify either this or inputs_embeds.
            inputs_embeds (`Optional[torch.Tensor]`):
                Tensor representing current input embeddings to the module. Must specify either this or input_ids.
            cache_position (`Optional[torch.Tensor]`):
                Tensor representing current input position in the cache. If not provided, a default tensor will be used.
            dynamic_shapes (`Optional[dict]`):
                Dynamic shapes to use for export if specified.
            strict(`Optional[bool]`):
                Flag to instruct `torch.export` to use `torchdynamo`.

        Returns:
            torch.export.ExportedProgram: The exported program that can be used for inference.

        Examples:
            Export with input_ids:
            ```python
            # Prepare inputs
            input_ids = torch.tensor([[1, 2, 3]], dtype=torch.long, device=model.device)
            cache_position = torch.arange(input_ids.shape[-1], dtype=torch.long, device=model.device)

            # Export
            exported = exportable_module.export(
                input_ids=input_ids,
                cache_position=cache_position
            )
            ```

            Export with inputs_embeds:
            ```python
            # Prepare embeddings
            inputs_embeds = torch.randn(1, 3, 768, device=model.device)  # batch_size=1, seq_len=3, hidden_size=768
            cache_position = torch.arange(inputs_embeds.shape[1], dtype=torch.long, device=model.device)

            # Export
            exported = exportable_module.export(
                inputs_embeds=inputs_embeds,
                cache_position=cache_position
            )
            ```
        """
        if not (input_ids is None) ^ (inputs_embeds is None):
            raise ValueError("Need to specify either input_ids or inputs_embeds.")

        if hasattr(self.model, "base_model_prefix"):
            base = getattr(self.model, self.model.base_model_prefix, self.model)
            model_device = base.device
        elif hasattr(self.model, "model"):
            model_device = self.model.model.device
        else:
            model_device = "cpu"
            logging.warning(
                "TorchExportableModuleForDecoderOnlyLM.export Can't infer device from the model. Set to CPU by default."
            )

        if input_ids is not None:
            input_kwargs = {
                "input_ids": input_ids,
                "cache_position": cache_position
                if cache_position is not None
                else torch.arange(input_ids.shape[-1], dtype=torch.long, device=model_device),
            }
        else:  # inputs_embeds
            input_kwargs = {
                "inputs_embeds": inputs_embeds,
                "cache_position": cache_position
                if cache_position is not None
                else torch.arange(inputs_embeds.shape[1], dtype=torch.long, device=model_device),
            }

        exported_program = torch.export.export(
            self.model,
            args=(),
            kwargs=input_kwargs,
            dynamic_shapes=dynamic_shapes,
            strict=strict if strict is not None else True,
        )

        return exported_program