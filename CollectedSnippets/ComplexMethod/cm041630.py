def prepare_model(self, model: HFModel) -> HFModel:
        if self.fsdp_mesh is None:
            logger.warning("No FSDP Mesh available, skipping FSDP wrapping.")
            return model

        mp_policy = self.get_mp_policy()
        layer_cls = get_transformer_layer_cls(model)

        if layer_cls is None:
            logger.warning(
                "Could not identify Transformer Layer class, applying FSDP to the whole model structure only."
            )
            transformer_layer_cls_to_wrap = set()
        else:
            logger.info(f"Applying per-layer FSDP to {layer_cls.__name__}")
            transformer_layer_cls_to_wrap = {layer_cls}

        if self.is_lora_module_wrap(model):
            lora_modules = []
            for module in model.modules():
                if len(list(module.children())) != 0:
                    continue
                if any(param.requires_grad for param in module.parameters(recurse=False)):
                    lora_modules.append(module)

            for module in lora_modules:
                fully_shard(
                    module,
                    mesh=self.fsdp_mesh,
                    reshard_after_forward=self.reshard_after_forward,
                    mp_policy=mp_policy,
                    offload_policy=CPUOffloadPolicy(pin_memory=self.pin_memory) if self.offload_params else None,
                )

            logger.info("Applying FSDP wrap for LoRA layer separately.")

        for name, module in model.named_modules():
            should_wrap = False

            if type(module) in transformer_layer_cls_to_wrap:
                should_wrap = True
            elif isinstance(module, nn.Embedding):
                if not getattr(model.config, "tie_word_embeddings", True):
                    should_wrap = True

            if should_wrap:
                fully_shard(
                    module,
                    mesh=self.fsdp_mesh,
                    reshard_after_forward=self.reshard_after_forward,
                    mp_policy=mp_policy,
                    offload_policy=CPUOffloadPolicy(pin_memory=self.pin_memory) if self.offload_params else None,
                )

        # BaseTrainer is the single source of truth for gradient checkpointing.
        # FSDP2 only applies the input-grad compatibility hook when checkpointing is already enabled.
        if getattr(model, "is_gradient_checkpointing", False):
            if self.rank == 0:
                logger.info("Gradient checkpointing is enabled. Applying FSDP2 input grad preparation.")

            if hasattr(model, "enable_input_require_grads"):
                model.enable_input_require_grads()
            else:

                def make_inputs_require_grad(module, input, output):
                    output.requires_grad_(True)

                model.get_input_embeddings().register_forward_hook(make_inputs_require_grad)

        fully_shard(
            model,
            mesh=self.fsdp_mesh,
            reshard_after_forward=self.reshard_after_forward,
            mp_policy=mp_policy,
            offload_policy=CPUOffloadPolicy(pin_memory=self.pin_memory) if self.offload_params else None,
        )

        return model