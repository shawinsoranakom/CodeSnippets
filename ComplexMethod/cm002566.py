def _process_fsdp_args(self):
        if not self.fsdp:
            self.fsdp = []
        elif self.fsdp is True:
            self.fsdp = [FSDPOption.FULL_SHARD]
        elif isinstance(self.fsdp, str):
            self.fsdp = [FSDPOption(s) for s in self.fsdp.split()]

        if self.fsdp == [FSDPOption.OFFLOAD]:
            raise ValueError(
                "`--fsdp offload` can't work on its own. It needs to be added to `--fsdp full_shard` or "
                '`--fsdp shard_grad_op`. For example, `--fsdp "full_shard offload"`.'
            )
        elif FSDPOption.FULL_SHARD in self.fsdp and FSDPOption.SHARD_GRAD_OP in self.fsdp:
            raise ValueError("`--fsdp full_shard` is not compatible with `--fsdp shard_grad_op`.")

        if self.gradient_checkpointing and (
            FSDPOption.FULL_SHARD in self.fsdp or FSDPOption.HYBRID_SHARD in self.fsdp
        ):
            logger.warning(
                "When using FSDP full shard, instead of using `gradient_checkpointing` in TrainingArguments, please"
                " use `activation_checkpointing` in `fsdp_config`. The former introduces a redundant AllGather"
                " operation in backward pass. Reference: https://github.com/huggingface/transformers/issues/30404"
            )

        if self.fsdp_config is None:
            self.fsdp_config = {}

        if isinstance(self.fsdp_config, str):
            if len(self.fsdp) == 0:
                warnings.warn("`--fsdp_config` is useful only when `--fsdp` is specified.")
            with open(self.fsdp_config, encoding="utf-8") as f:
                self.fsdp_config = json.load(f)

        if self.fsdp_config is not None and isinstance(self.fsdp_config, dict):
            for k in list(self.fsdp_config.keys()):
                if k.startswith("fsdp_"):
                    v = self.fsdp_config.pop(k)
                    self.fsdp_config[k[5:]] = v

        self.fsdp_config["min_num_params"] = self.fsdp_config.get("min_num_params", 0)

        # Normalize transformer_layer_cls_to_wrap from string to list
        if isinstance(self.fsdp_config.get("transformer_layer_cls_to_wrap", None), str):
            self.fsdp_config["transformer_layer_cls_to_wrap"] = [self.fsdp_config["transformer_layer_cls_to_wrap"]]

        if len(self.fsdp) == 0 and self.fsdp_config["min_num_params"] > 0:
            warnings.warn("`min_num_params` is useful only when `--fsdp` is specified.")

        if len(self.fsdp) == 0 and self.fsdp_config.get("transformer_layer_cls_to_wrap", None) is not None:
            warnings.warn("`transformer_layer_cls_to_wrap` is useful only when `--fsdp` is specified.")

        if (
            len(self.fsdp) > 0
            and self.fsdp_config["min_num_params"] > 0
            and self.fsdp_config.get("transformer_layer_cls_to_wrap", None) is not None
        ):
            raise ValueError("`min_num_params` and `transformer_layer_cls_to_wrap` are mutually exclusive.")
        self.fsdp_config["xla"] = self.fsdp_config.get("xla", False)
        self.fsdp_config["xla_fsdp_v2"] = self.fsdp_config.get("xla_fsdp_v2", False)
        self.fsdp_config["xla_fsdp_grad_ckpt"] = self.fsdp_config.get("xla_fsdp_grad_ckpt", False)
        if self.fsdp_config["xla"]:
            if len(self.fsdp) > 0:
                # Copy to avoid mutating the original (needed for JSON serialization)
                self.xla_fsdp_config = self.fsdp_config.get("xla_fsdp_settings", {}).copy()
                # Convert string dtype names to torch.dtype
                if "compute_dtype" in self.xla_fsdp_config:
                    self.xla_fsdp_config["compute_dtype"] = getattr(torch, self.xla_fsdp_config["compute_dtype"])
                if "buffer_dtype" in self.xla_fsdp_config:
                    self.xla_fsdp_config["buffer_dtype"] = getattr(torch, self.xla_fsdp_config["buffer_dtype"])
            else:
                warnings.warn("XLA FSDP can be used only when `--fsdp` is specified.")
        else:
            if self.fsdp_config["xla_fsdp_grad_ckpt"]:
                warnings.warn("`--xla_fsdp_grad_ckpt` is useful only when `--xla` is set to true.")

        # Build kwargs for Accelerate's FSDPPlugin
        fsdp_plugin_args = None
        if len(self.fsdp) > 0 and not self.fsdp_config["xla"]:
            from accelerate.utils.constants import (
                FSDP_AUTO_WRAP_POLICY,
                FSDP_SHARDING_STRATEGY,
            )

            fsdp_plugin_args = {}
            fsdp_sharding = None
            for fsdp_option in self.fsdp:
                if fsdp_option.upper() in FSDP_SHARDING_STRATEGY:
                    fsdp_sharding = fsdp_option
                elif fsdp_option == FSDPOption.OFFLOAD:
                    fsdp_plugin_args["cpu_offload"] = True
                elif fsdp_option == FSDPOption.AUTO_WRAP:
                    fsdp_plugin_args["auto_wrap_policy"] = FSDP_AUTO_WRAP_POLICY[0]
                    if self.fsdp_config["min_num_params"] > 0:
                        fsdp_plugin_args["min_num_params"] = self.fsdp_config["min_num_params"]
                        fsdp_plugin_args["auto_wrap_policy"] = FSDP_AUTO_WRAP_POLICY[1]
                    elif self.fsdp_config.get("transformer_layer_cls_to_wrap", None) is not None:
                        fsdp_plugin_args["transformer_cls_names_to_wrap"] = ",".join(
                            self.fsdp_config["transformer_layer_cls_to_wrap"]
                        )
            fsdp_version = int(self.fsdp_config.get("version", 1))
            fsdp_plugin_args["fsdp_version"] = fsdp_version
            prefetch_policy = self.fsdp_config.get("backward_prefetch", "NO_PREFETCH")
            if fsdp_version == 2:
                # full_shard → True (reshard after forward), shard_grad_op → False
                default_reshard = fsdp_sharding != "shard_grad_op" if fsdp_sharding else True
                fsdp_plugin_args["reshard_after_forward"] = str_to_bool(
                    str(self.fsdp_config.get("reshard_after_forward", default_reshard)).lower()
                )
            else:
                fsdp_plugin_args["forward_prefetch"] = str_to_bool(
                    str(self.fsdp_config.get("forward_prefetch", "false")).lower()
                )
                fsdp_plugin_args["backward_prefetch"] = prefetch_policy.upper()
                # Pass sharding strategy as reshard_after_forward (accelerate converts it to ShardingStrategy)
                default_reshard = fsdp_sharding.upper() if fsdp_sharding else "FULL_SHARD"
                fsdp_plugin_args["reshard_after_forward"] = str(
                    self.fsdp_config.get("reshard_after_forward", default_reshard)
                ).lower()
                fsdp_plugin_args["use_orig_params"] = str_to_bool(
                    str(self.fsdp_config.get("use_orig_params", "true")).lower()
                )

            sync_module_states = str(self.fsdp_config.get("sync_module_states", "true")).lower()
            cpu_ram_efficient_loading = str(self.fsdp_config.get("cpu_ram_efficient_loading", "false")).lower()
            if sync_module_states == "false" and cpu_ram_efficient_loading == "true":
                # Without sync, non-main processes would have random weights
                raise ValueError('`sync_module_states` must be `"True"` if `cpu_ram_efficient_loading` is `"True"`')

            # Set env var to suppress Accelerate warning and for transformers to read
            fsdp_plugin_args["cpu_ram_efficient_loading"] = str_to_bool(cpu_ram_efficient_loading)
            os.environ["FSDP_CPU_RAM_EFFICIENT_LOADING"] = cpu_ram_efficient_loading

            fsdp_plugin_args["sync_module_states"] = str_to_bool(sync_module_states)

        return fsdp_plugin_args