def load_adapter(
        self,
        peft_model_id: str | None = None,
        adapter_name: str | None = None,
        peft_config: dict[str, Any] | None = None,
        adapter_state_dict: dict[str, "torch.Tensor"] | None = None,
        low_cpu_mem_usage: bool = False,
        is_trainable: bool = False,
        hotswap: bool | Literal["auto"] = "auto",
        local_files_only: bool = False,
        adapter_kwargs: dict[str, Any] | None = None,
        load_config: Optional["LoadStateDictConfig"] = None,
        **kwargs,
    ) -> None:
        """
        Load adapter weights from file or remote Hub folder. If you are not familiar with adapters and PEFT methods, we
        invite you to read more about them on PEFT official documentation: https://huggingface.co/docs/peft

        Requires PEFT to be installed as a backend to load the adapter weights.

        Args:
            peft_model_id (`str`, *optional*):
                The identifier of the model to look for on the Hub, or a local path to the saved adapter config file
                and adapter weights.
            adapter_name (`str`, *optional*):
                The adapter name to use. If not set, will use the name "default".
            load_config (`LoadStateDictConfig`, *optional*):
                A load configuration to reuse when pulling adapter weights, typically from `from_pretrained`.
            kwargs (`dict[str, Any]`, *optional*):
                Additional `LoadStateDictConfig` fields passed as keyword arguments.
            peft_config (`dict[str, Any]`, *optional*):
                The configuration of the adapter to add, supported adapters are all non-prompt learning configs (LoRA,
                IA³, etc). This argument is used in case users directly pass PEFT state dicts.
            adapter_state_dict (`dict[str, torch.Tensor]`, *optional*):
                The state dict of the adapter to load. This argument is used in case users directly pass PEFT state
                dicts.
            low_cpu_mem_usage (`bool`, *optional*, defaults to `False`):
                Reduce memory usage while loading the PEFT adapter. This should also speed up the loading process.
            is_trainable (`bool`, *optional*, defaults to `False`):
                Whether the adapter should be trainable or not. If `False`, the adapter will be frozen and can only be
                used for inference.
            hotswap : (`"auto"` or `bool`, *optional*, defaults to `"auto"`)
                Whether to substitute an existing (LoRA) adapter with the newly loaded adapter in-place. This means
                that, instead of loading an additional adapter, this will take the existing adapter weights and replace
                them with the weights of the new adapter. This can be faster and more memory efficient. However, the
                main advantage of hotswapping is that when the model is compiled with torch.compile, loading the new
                adapter does not require recompilation of the model. When using hotswapping, the passed `adapter_name`
                should be the name of an already loaded adapter.

                If the new adapter and the old adapter have different ranks and/or LoRA alphas (i.e. scaling), you need
                to call an additional method before loading the adapter:

                ```py
                model = AutoModel.from_pretrained(...)
                max_rank = ...  # the highest rank among all LoRAs that you want to load
                # call *before* compiling and loading the LoRA adapter
                model.enable_peft_hotswap(target_rank=max_rank)
                model.load_adapter(file_name_1, adapter_name="default")
                # optionally compile the model now
                model = torch.compile(model, ...)
                output_1 = model(...)
                # now you can hotswap the 2nd adapter, use the same name as for the 1st
                # hotswap is activated by default since enable_peft_hotswap was called
                model.load_adapter(file_name_2, adapter_name="default")
                output_2 = model(...)
                ```

                By default, hotswap is disabled and requires passing `hotswap=True`. If you called
                `enable_peft_hotswap` first, it is enabled. You can still manually disable it in that case by passing
                `hotswap=False`.

                Note that hotswapping comes with a couple of limitations documented here:
                https://huggingface.co/docs/peft/main/en/package_reference/hotswap
            adapter_kwargs (`dict[str, Any]`, *optional*):
                Additional keyword arguments passed along to the `from_pretrained` method of the adapter config and
                `find_adapter_config_file` method.
        """
        from peft import PeftType
        from peft.utils.save_and_load import _maybe_shard_state_dict_for_tp

        from ..modeling_utils import LoadStateDictConfig, _get_resolved_checkpoint_files, load_state_dict

        if local_files_only:
            kwargs["local_files_only"] = True
        base_load_config = load_config.__dict__ if load_config is not None else {}
        base_load_config.update(kwargs)
        base_load_config.setdefault("pretrained_model_name_or_path", None)
        load_config = LoadStateDictConfig(**base_load_config)
        peft_model_id = peft_model_id or load_config.pretrained_model_name_or_path

        if hotswap == "auto":
            # if user called model.enable_peft_hotswap and this is not the first adapter, enable hotswap
            hotswap_enabled = getattr(self, "_hotswap_enabled", False)
            not_first_adapter = bool(self._hf_peft_config_loaded and (adapter_name in self.peft_config))
            hotswap = hotswap_enabled and not_first_adapter

        if hotswap:
            if (not self._hf_peft_config_loaded) or (adapter_name not in self.peft_config):
                raise ValueError(
                    "To hotswap an adapter, there must already be an existing adapter with the same adapter name."
                )
            if any(conf.peft_type != PeftType.LORA for conf in self.peft_config.values()):
                raise ValueError("Hotswapping is currently only supported for LoRA, please set `hotswap=False`.")

        adapter_name = adapter_name if adapter_name is not None else "default"
        adapter_kwargs = adapter_kwargs or {}

        from peft import PeftConfig, inject_adapter_in_model

        if self._hf_peft_config_loaded and (not hotswap) and (adapter_name in self.peft_config):
            raise ValueError(f"Adapter with name {adapter_name} already exists. Please use a different name.")
        elif hotswap and ((not self._hf_peft_config_loaded) or (adapter_name not in self.peft_config)):
            raise ValueError(
                "To hotswap an adapter, there must already be an existing adapter with the same adapter name."
            )

        if peft_model_id is None and (adapter_state_dict is None and peft_config is None):
            raise ValueError(
                "You should either pass a `peft_model_id` or a `peft_config` and `adapter_state_dict` to load an adapter."
            )

        if peft_config is None:
            load_config.download_kwargs.update(**adapter_kwargs)
            adapter_config_file = find_adapter_config_file(
                peft_model_id,
                **load_config.download_kwargs,
            )

            if adapter_config_file is None:
                raise ValueError(
                    f"adapter model file not found in {peft_model_id}. Make sure you are passing the correct path to the "
                    "adapter model."
                )

            peft_config = PeftConfig.from_pretrained(
                peft_model_id,
                **load_config.download_kwargs,
            )

        weight_conversions = get_model_conversion_mapping(self)

        # TODO: remove once PEFT < 0.19 is dropped, use peft.utils.transformers_weight_conversion
        peft_config = convert_peft_config_for_transformers(peft_config, model=self, conversions=weight_conversions)

        if hasattr(peft_config, "inference_mode"):
            peft_config.inference_mode = not is_trainable

        peft_weight_conversions = build_peft_weight_mapping(weight_conversions, adapter_name, peft_config=peft_config)

        patch_moe_parameter_targeting(model=self, peft_config=peft_config)

        if not hotswap:
            # Create and add fresh new adapters into the model, unless the weights are hotswapped
            inject_adapter_in_model(peft_config, self, adapter_name)

        if not self._hf_peft_config_loaded:
            self._hf_peft_config_loaded = True

        if adapter_state_dict is None:
            adapter_filenames = ["adapter_model.safetensors", "adapter_model.bin"]
            if load_config.use_safetensors is False:
                adapter_filenames.reverse()

            checkpoint_files = sharded_metadata = None
            last_error = None
            for adapter_filename in adapter_filenames:
                try:
                    checkpoint_files, sharded_metadata = _get_resolved_checkpoint_files(
                        pretrained_model_name_or_path=peft_model_id,
                        variant=None,
                        gguf_file=None,
                        use_safetensors=(
                            load_config.use_safetensors if adapter_filename.endswith(".safetensors") else False
                        ),
                        user_agent=None,
                        is_remote_code=False,
                        transformers_explicit_filename=adapter_filename,
                        download_kwargs=load_config.download_kwargs,
                    )
                    break
                except OSError as error:
                    last_error = error

            if checkpoint_files is None:
                raise last_error or OSError("Could not download either a .bin or a .safetensors adapter file.")
        else:
            checkpoint_files, sharded_metadata = [], {}

        device_map = getattr(self, "hf_device_map", {"": self.device})

        # If the model is tensor parallel, we handle the sharding of the state dict here since the logic in `self._load_pretrained_model`
        # is not compatible with the way PEFT adapter should be sharded.
        has_tp_adapters = False
        for module in self.modules():
            tp_info = getattr(module, "_tp_info", None)
            if tp_info is not None:
                has_tp_adapters = True
                break

        if has_tp_adapters:
            all_pointer = set()
            if adapter_state_dict is not None:
                merged_state_dict = adapter_state_dict
            elif (
                checkpoint_files is not None
                and checkpoint_files[0].endswith(".safetensors")
                and adapter_state_dict is None
            ):
                merged_state_dict = {}
                for file in checkpoint_files:
                    file_pointer = safe_open(file, framework="pt", device="cpu")
                    all_pointer.add(file_pointer)
                    for k in file_pointer.keys():
                        merged_state_dict[k] = file_pointer.get_tensor(k)
            # Checkpoints are .bin
            elif checkpoint_files is not None:
                merged_state_dict = {}
                for ckpt_file in checkpoint_files:
                    merged_state_dict.update(load_state_dict(ckpt_file))
            else:
                raise ValueError("Neither a state dict nor checkpoint files were found.")

            adapter_state_dict = merged_state_dict

            if any(not isinstance(v, torch.Tensor) for v in adapter_state_dict.values()):
                raise ValueError("Expected all values in the adapter state dict to be tensors.")

            _maybe_shard_state_dict_for_tp(self, adapter_state_dict, adapter_name)

        load_config = replace(
            load_config,
            pretrained_model_name_or_path=peft_model_id,
            sharded_metadata=sharded_metadata,
            weight_mapping=peft_weight_conversions,
            device_map=device_map,
        )

        loading_info, _ = self._load_pretrained_model(
            model=self,
            state_dict=adapter_state_dict,
            checkpoint_files=checkpoint_files,
            load_config=load_config,
            # pass expected keys explicitly, otherwise they are determined from the state_dict, which can contain
            # unexpected entries, like "layer.SCB" from a bnb layer.
            expected_keys=[n for n, _ in self.named_parameters()],
        )

        if peft_config.inference_mode:
            from peft.tuners.tuners_utils import BaseTunerLayer

            self.eval()
            for module in self.modules():
                if isinstance(module, BaseTunerLayer):
                    module.requires_grad_(False)

        adapter_key_markers = {adapter_name}
        if peft_config is not None and getattr(peft_config, "peft_type", None) is not None:
            adapter_key_markers.add(peft_config.peft_type.value.lower())

        def is_adapter_key(key: str) -> bool:
            return any(marker in key for marker in adapter_key_markers)

        loading_info.missing_keys = {k for k in loading_info.missing_keys if is_adapter_key(k)}

        log_state_dict_report(
            model=self,
            pretrained_model_name_or_path=load_config.pretrained_model_name_or_path,
            ignore_mismatched_sizes=load_config.ignore_mismatched_sizes,
            loading_info=loading_info,
            logger=logger,
        )