def _create_lora_modules(self):
        def _parent_module(module_name: str) -> str:
            # module name is a dot separated name.
            # for example:
            #  - given an input 'x.y.z' return 'x.y'
            #  - given an input 'x' return ''
            return module_name.rpartition(".")[0]

        for module_name, module in self.model.named_modules(remove_duplicate=False):
            if isinstance(module, PPMissingLayer):
                continue

            if not self._match_target_modules(module_name):
                continue

            punica_wrapper = self._get_punica_wrapper(module_name)
            if punica_wrapper is None:
                logger.warning(
                    "Regarding %s, no matching PunicaWrapper "
                    "is found; %s will be ignored.",
                    self.model.__class__.__name__,
                    module_name,
                )
                continue

            # TODO: Remove this restriction
            # peft error when generating LoRA adapter with "gate" module:
            # "Target module NemotronHTopkRouter() is not supported."
            # Working LoRA adapter was created using peft with:
            # LoraConfig(target_modules="all-linear", ...)
            if self._is_non_gated_moe and module_name.endswith("mixer.gate"):
                logger.debug_once(
                    "LoRA is not supported for non-gated MoE gate module."
                    " %s will be ignored.",
                    module_name,
                )
                continue

            parts = module_name.split(".")[-1]
            packed_moduled_lst = self.packed_modules_mapping.get(parts, [])
            if isinstance(module, FusedMoE):
                # packed_moduled_lst is used here to just determine whether to
                # instantiate FusedMoE3DWithLoRA or FusedMoEWithLoRA, and the
                # difference between these two LoRA layers is whether the
                # LoRA weights of w1 and w3 have already been fused on disk.

                packed_moduled_lst = ["w13"] if self._is_3d_moe_model else ["w1", "w3"]
            new_module = replace_submodule(
                self.model,
                module_name,
                from_layer(
                    module,
                    self.lora_slots,
                    self.lora_config,
                    packed_moduled_lst,
                    self.model.config,
                ),
            )

            # (yard1): TODO make this more robust
            if "lm_head" in module_name:
                logits_processor_module_name = "logits_processor"
                parent_module = _parent_module(module_name)
                if parent_module:
                    logits_processor_module_name = (
                        f"{parent_module}.{logits_processor_module_name}"
                    )

                logits_processor_module = self.model.get_submodule(
                    logits_processor_module_name
                )

                new_module = replace_submodule(
                    self.model,
                    logits_processor_module_name,
                    from_layer_logits_processor(
                        logits_processor_module,
                        module,
                        self.lora_slots,
                        self.lora_config,
                        self.model.config,
                    ),
                )

            # Some matched modules can be unsupported by LoRA wrappers
            # (e.g. subclasses with specialized forward behavior).
            if not isinstance(new_module, BaseLayerWithLoRA):
                error_msg = (
                    "LoRA target module "
                    f"{module_name} ({type(module).__name__}) matched the "
                    "deployment configuration but could not be wrapped by any "
                    "LoRA layer implementation."
                )
                if self.lora_config.target_modules is not None:
                    raise ValueError(
                        f"{error_msg} target_modules="
                        f"{sorted(self.lora_config.target_modules)}"
                    )
                logger.warning_once("%s It will be ignored.", error_msg)
                continue
            self.register_module(module_name, new_module)

            self._register_packed_modules(module_name)
            # All lora layers share the same punica_wrapper based on reference.
            new_module.set_mapping(punica_wrapper)