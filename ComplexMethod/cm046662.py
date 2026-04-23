def _apply_adapter_state(self, use_adapter: Optional[Union[bool, str]]) -> None:
        """
        Apply adapter state before generation. Must be called under _generation_lock.

        Uses PEFT's disable_adapter_layers() / enable_adapter_layers() which toggle
        a boolean flag on each LoRA layer. Unsloth's fast_linear_forward checks this
        flag (proj.disable_adapters) and skips LoRA computation when True.
        This is non-destructive — no model unloading/reloading needed.

        Args:
            use_adapter: None = no change, False = disable (base model),
                         True = enable current adapter, str = enable specific adapter.
        """
        if use_adapter is None:
            return

        base = self.active_model_name
        if not base or base not in self.models:
            return

        model_info = self.models[base]
        model = model_info.get("model")
        if model is None:
            return

        if use_adapter is False:
            # Disable LoRA layers → base model output
            if isinstance(model, (PeftModel, PeftModelForCausalLM)):
                logger.info(
                    f"Compare mode: disabling adapters on '{base}' for base model generation"
                )
                model.base_model.disable_adapter_layers()
            else:
                logger.info(
                    f"Compare mode: model '{base}' is not a PeftModel, already base"
                )

        elif use_adapter is True:
            # Re-enable LoRA layers → adapter output
            if isinstance(model, (PeftModel, PeftModelForCausalLM)):
                logger.info(
                    f"Compare mode: enabling adapters on '{base}' for LoRA generation"
                )
                model.base_model.enable_adapter_layers()
            else:
                logger.warning("use_adapter=true but model is not a PeftModel")

        elif isinstance(use_adapter, str):
            # Enable adapters and set the specific one active
            if isinstance(model, (PeftModel, PeftModelForCausalLM)):
                logger.info(
                    f"Compare mode: enabling adapter '{use_adapter}' on '{base}'"
                )
                model.base_model.enable_adapter_layers()
                self.set_active_adapter(base, use_adapter)
            else:
                logger.warning(
                    f"use_adapter='{use_adapter}' but model is not a PeftModel"
                )