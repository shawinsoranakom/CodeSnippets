def from_pretrained(
        cls: type[SpecificPreTrainedModelType],
        pretrained_model_name_or_path: str | os.PathLike | None,
        *model_args,
        config: PreTrainedConfig | str | os.PathLike | None = None,
        cache_dir: str | os.PathLike | None = None,
        ignore_mismatched_sizes: bool = False,
        force_download: bool = False,
        local_files_only: bool = False,
        token: str | bool | None = None,
        revision: str = "main",
        use_safetensors: bool | None = None,
        weights_only: bool = True,
        fusion_config: dict[str, bool | dict[str, Any]] | None = None,
        disable_mmap: bool | None = None,
        **kwargs,
    ) -> SpecificPreTrainedModelType:
        r"""
        Instantiate a pretrained pytorch model from a pre-trained model configuration.

        The model is set in evaluation mode by default using `model.eval()` (Dropout modules are deactivated). To train
        the model, you should first set it back in training mode with `model.train()`.

        The warning *Weights from XXX not initialized from pretrained model* means that the weights of XXX do not come
        pretrained with the rest of the model. It is up to you to train those weights with a downstream fine-tuning
        task.

        The warning *Weights from XXX not used in YYY* means that the layer XXX is not used by YYY, therefore those
        weights are discarded.

        Parameters:
            pretrained_model_name_or_path (`str` or `os.PathLike`, *optional*):
                Can be either:

                    - A string, the *model id* of a pretrained model hosted inside a model repo on huggingface.co.
                    - A path to a *directory* containing model weights saved using
                      [`~PreTrainedModel.save_pretrained`], e.g., `./my_model_directory/`.
                    - `None` if you are both providing the configuration and state dictionary (resp. with keyword
                      arguments `config` and `state_dict`).
            model_args (sequence of positional arguments, *optional*):
                All remaining positional arguments will be passed to the underlying model's `__init__` method.
            config (`Union[PreTrainedConfig, str, os.PathLike]`, *optional*):
                Can be either:

                    - an instance of a class derived from [`PreTrainedConfig`],
                    - a string or path valid as input to [`~PreTrainedConfig.from_pretrained`].

                Configuration for the model to use instead of an automatically loaded configuration. Configuration can
                be automatically loaded when:

                    - The model is a model provided by the library (loaded with the *model id* string of a pretrained
                      model).
                    - The model was saved using [`~PreTrainedModel.save_pretrained`] and is reloaded by supplying the
                      save directory.
                    - The model is loaded by supplying a local directory as `pretrained_model_name_or_path` and a
                      configuration JSON file named *config.json* is found in the directory.
            state_dict (`dict[str, torch.Tensor]`, *optional*):
                A state dictionary to use instead of a state dictionary loaded from saved weights file.

                This option can be used if you want to create a model from a pretrained configuration but load your own
                weights. In this case though, you should check if using [`~PreTrainedModel.save_pretrained`] and
                [`~PreTrainedModel.from_pretrained`] is not a simpler option.
            cache_dir (`Union[str, os.PathLike]`, *optional*):
                Path to a directory in which a downloaded pretrained model configuration should be cached if the
                standard cache should not be used.
            ignore_mismatched_sizes (`bool`, *optional*, defaults to `False`):
                Whether or not to raise an error if some of the weights from the checkpoint do not have the same size
                as the weights of the model (if for instance, you are instantiating a model with 10 labels from a
                checkpoint with 3 labels).
            force_download (`bool`, *optional*, defaults to `False`):
                Whether or not to force the (re-)download of the model weights and configuration files, overriding the
                cached versions if they exist.
            proxies (`dict[str, str]`, *optional*):
                A dictionary of proxy servers to use by protocol or endpoint, e.g., `{'http': 'foo.bar:3128',
                'http://hostname': 'foo.bar:4012'}`. The proxies are used on each request.
            output_loading_info(`bool`, *optional*, defaults to `False`):
                Whether or not to also return a dictionary containing missing keys, unexpected keys and error messages.
            local_files_only(`bool`, *optional*, defaults to `False`):
                Whether or not to only look at local files (i.e., do not try to download the model).
            token (`str` or `bool`, *optional*):
                The token to use as HTTP bearer authorization for remote files. If `True`, or not specified, will use
                the token generated when running `hf auth login` (stored in `~/.huggingface`).
            revision (`str`, *optional*, defaults to `"main"`):
                The specific model version to use. It can be a branch name, a tag name, or a commit id, since we use a
                git-based system for storing models and other artifacts on huggingface.co, so `revision` can be any
                identifier allowed by git.

                <Tip>

                To test a pull request you made on the Hub, you can pass `revision="refs/pr/<pr_number>"`.

                </Tip>
            attn_implementation (`str`, *optional*):
                The attention implementation to use in the model (if relevant). Can be any of
                    - `"eager"` (manual implementation of the attention)
                    - `"sdpa"` (using [`F.scaled_dot_product_attention`](https://pytorch.org/docs/master/generated/torch.nn.functional.scaled_dot_product_attention.html))
                    - `"flash_attention_2"` (using [Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention))
                    - `"flash_attention_3"` (using [Dao-AILab/flash-attention/hopper](https://github.com/Dao-AILab/flash-attention/tree/main/hopper))
                    - `"flash_attention_4"` (using [Dao-AILab/flash-attention/flash_attn/cute](https://github.com/Dao-AILab/flash-attention/tree/main/flash_attn/cute)).
                By default, if available, SDPA will be used. The default is otherwise the manual `"eager"` implementation.

                Accept HF kernel references in the form:
                  <namespace>/<repo_name>[@<revision>][:<kernel_name>]

                - <namespace> and <repo_name> are any non-"/" and non-":" sequences.
                - "@<revision>" is optional (branch, tag, or commit-ish), e.g. "@main", "@v1.2.0", "@abc123".
                - ":<kernel_name>" is optional and selects a function inside the kernel repo.
                - Both options can appear together and in this order only: @revision first, then :kernel_name.
                - We intentionally allow a leading "<wrapper>|" prefix (e.g., "flash|...") because the code
                  strips it before loading; '|' is not excluded in the character classes here.

                Examples that match:
                  "org/model"
                  "org/model@main"
                  "org/model:custom_kernel"
                  "org/model@v1.2.3:custom_kernel"
            experts_implementation (`str`, *optional*):
                The experts implementation to use in the model (if relevant). Can be any of:

                - `"eager"` (sequential implementation of the experts matrix multiplications).
                - `"batched_mm"` (using [`torch.bmm`](https://pytorch.org/docs/stable/generated/torch.bmm.html)).
                - `"grouped_mm"` (using [`torch.nn.functional.grouped_mm`](https://docs.pytorch.org/docs/main/generated/torch.nn.functional.grouped_mm.html)).

                By default, if the model supports it, `"grouped_mm"` will be used. The default is otherwise the manual `"eager"` implementation.

            > Parameters for big model inference

            dtype (`str` or `torch.dtype`, *optional*, defaults to `"auto"`):
                Override the default `torch_dtype` and load the model under a specific `dtype`. The different options
                are:

                1. `torch.float16` or `torch.bfloat16` or `torch.float`: load in a specified
                  `dtype`, ignoring the model's `config.dtype` if one exists. If not specified
                  - the model will get loaded in `torch.float` (fp32).

                2. `"auto"` - A `dtype` or `torch_dtype` entry in the `config.json` file of the model will be
                  attempted to be used. If this entry isn't found then next check the `dtype` of the first weight in
                  the checkpoint that's of a floating point type and use that as `dtype`. This will load the model
                  using the `dtype` it was saved in at the end of the training. It can't be used as an indicator of how
                  the model was trained. Since it could be trained in one of half precision dtypes, but saved in fp32.

                3. A string that is a valid `torch.dtype`. E.g. "float32" loads the model in `torch.float32`, "float16" loads in `torch.float16` etc.

                <Tip>

                For some models the `dtype` they were trained in is unknown - you may try to check the model's paper or
                reach out to the authors and ask them to add this information to the model's card and to insert the
                `dtype` or `torch_dtype` entry in `config.json` on the hub.

                </Tip>

            device_map (`str` or `dict[str, Union[int, str, torch.device]]` or `int` or `torch.device`, *optional*):
                A map that specifies where each submodule should go. It doesn't need to be refined to each
                parameter/buffer name, once a given module name is inside, every submodule of it will be sent to the
                same device. If we only pass the device (*e.g.*, `"cpu"`, `"cuda:1"`, `"mps"`, or a GPU ordinal rank
                like `1`) on which the model will be allocated, the device map will map the entire model to this
                device. Passing `device_map = 0` means put the whole model on GPU 0.

                To have Accelerate compute the most optimized `device_map` automatically, set `device_map="auto"`. For
                more information about each option see [designing a device
                map](https://hf.co/docs/accelerate/main/en/usage_guides/big_modeling#designing-a-device-map).
            max_memory (`Dict`, *optional*):
                A dictionary device identifier to maximum memory if using `device_map`. Will default to the maximum memory available for each
                GPU and the available CPU RAM if unset.
            tp_plan (`Optional[Union[dict, str]]`, *optional*):
                A torch tensor parallel plan, see [here](https://pytorch.org/tutorials/intermediate/TP_tutorial.html). Use `tp_plan="auto"` to
                use the predefined plan based on the model. If it's a dict, then it should match between module names and desired layout.
                Note that if you use it, you should launch your script accordingly with `torchrun [args] script.py`. This will be much
                faster than using a `device_map`, but has limitations.
            tp_size (`str`, *optional*):
                A torch tensor parallel degree. If not provided would default to world size.
            device_mesh (`torch.distributed.DeviceMesh`, *optional*):
                A torch device mesh. If not provided would default to world size. Used only for tensor parallel for now.
                If provided, it has to contain dimension named `"tp"` in case it's > 1 dimensional, this dimension will be used for tensor parallelism
            offload_folder (`str` or `os.PathLike`, *optional*):
                If the `device_map` contains any value `"disk"`, the folder where we will offload weights.
            offload_buffers (`bool`, *optional*):
                Whether or not to offload the buffers with the model parameters.
            quantization_config (`Union[QuantizationConfigMixin,Dict]`, *optional*):
                A dictionary of configuration parameters or a QuantizationConfigMixin object for quantization (e.g
                bitsandbytes, gptq).
            subfolder (`str`, *optional*, defaults to `""`):
                In case the relevant files are located inside a subfolder of the model repo on huggingface.co, you can
                specify the folder name here.
            variant (`str`, *optional*):
                If specified load weights from `variant` filename, *e.g.* pytorch_model.<variant>.bin.
            use_safetensors (`bool`, *optional*, defaults to `None`):
                Whether or not to use `safetensors` checkpoints. Defaults to `None`. If not specified and `safetensors`
                is not installed, it will be set to `False`.
            weights_only (`bool`, *optional*, defaults to `True`):
                Indicates whether unpickler should be restricted to loading only tensors, primitive types,
                dictionaries and any types added via torch.serialization.add_safe_globals().
                When set to False, we can load wrapper tensor subclass weights.
            disable_mmap (`bool`, *optional*):
                Whether to disable memory mapping when loading safetensors checkpoints. When `None` (default),
                it is auto-detected to `True` when the checkpoint lives on an `hf-mount` FUSE filesystem
                (used by HF Spaces/Endpoints), where mmap + parallel page-faults can deadlock. When `True`,
                files are read fully into memory and parsed with `safetensors.torch.load`. When `False`, the
                default memory-mapped loader is always used.
            fusion_config (`dict[str, bool | dict[str, Any]]`, *optional*):
                Optional fusion configuration applied before model instantiation. Each key enables a fusion family and
                its value can either be `True` to enable that fusion with default options or a dictionary of
                family-specific options. For example, `{"patch_embeddings": True}` enables patch embedding fusion.
                This should only be used as an inference optimization, as it can slightly change outputs. If omitted,
                `from_pretrained()` falls back to `config.fusion_config` when available. Refer to the fusion mapping
                guide in `docs/source/en/fusion_mapping.md` for more details.
            key_mapping (`dict[str, str], *optional*):
                A potential mapping of the weight names if using a model on the Hub which is compatible to a Transformers
                architecture, but was not converted accordingly.
            kwargs (remaining dictionary of keyword arguments, *optional*):
                Can be used to update the configuration object (after it being loaded) and initiate the model (e.g.,
                `output_attentions=True`). Behaves differently depending on whether a `config` is provided or
                automatically loaded:

                    - If a configuration is provided with `config`, `**kwargs` will be directly passed to the
                      underlying model's `__init__` method (we assume all relevant updates to the configuration have
                      already been done)
                    - If a configuration is not provided, `kwargs` will be first passed to the configuration class
                      initialization function ([`~PreTrainedConfig.from_pretrained`]). Each key of `kwargs` that
                      corresponds to a configuration attribute will be used to override said attribute with the
                      supplied `kwargs` value. Remaining keys that do not correspond to any configuration attribute
                      will be passed to the underlying model's `__init__` function.

        <Tip>

        Activate the special ["offline-mode"](https://huggingface.co/transformers/installation.html#offline-mode) to
        use this method in a firewalled environment.

        </Tip>

        Examples:

        ```python
        >>> from transformers import BertConfig, BertModel

        >>> # Download model and configuration from huggingface.co and cache.
        >>> model = BertModel.from_pretrained("google-bert/bert-base-uncased")
        >>> # Model was saved using *save_pretrained('./test/saved_model/')* (for example purposes, not runnable).
        >>> model = BertModel.from_pretrained("./test/saved_model/")
        >>> # Update configuration during loading.
        >>> model = BertModel.from_pretrained("google-bert/bert-base-uncased", output_attentions=True)
        >>> assert model.config.output_attentions == True
        ```
        """
        state_dict = kwargs.pop("state_dict", None)
        proxies = kwargs.pop("proxies", None)
        tqdm_class = kwargs.pop("tqdm_class", None)
        output_loading_info = kwargs.pop("output_loading_info", False)
        from_pipeline = kwargs.pop("_from_pipeline", None)
        from_auto_class = kwargs.pop("_from_auto", False)
        dtype = kwargs.pop("dtype", None)
        torch_dtype = kwargs.pop("torch_dtype", None)  # kept for BC
        device_map = kwargs.pop("device_map", None)
        max_memory = kwargs.pop("max_memory", None)
        offload_folder = kwargs.pop("offload_folder", None)
        offload_buffers = kwargs.pop("offload_buffers", False)
        quantization_config = kwargs.pop("quantization_config", None)
        subfolder = kwargs.pop("subfolder", "")
        commit_hash = kwargs.pop("_commit_hash", None)
        variant = kwargs.pop("variant", None)
        adapter_kwargs = (kwargs.pop("adapter_kwargs", {}) or {}).copy()
        adapter_name = kwargs.pop("adapter_name", "default")
        generation_config = kwargs.pop("generation_config", None)
        gguf_file = kwargs.pop("gguf_file", None)
        tp_plan = kwargs.pop("tp_plan", None)
        tp_size = kwargs.pop("tp_size", None)
        distributed_config: DistributedConfig = kwargs.pop("distributed_config", None)
        device_mesh = kwargs.pop("device_mesh", None)
        trust_remote_code = kwargs.pop("trust_remote_code", None)
        allow_all_kernels = kwargs.pop("allow_all_kernels", False)
        use_kernels = kwargs.pop("use_kernels", False)
        kernel_config = kwargs.pop("kernel_config", None)
        key_mapping = kwargs.pop("key_mapping", None)

        if distributed_config is not None and tp_plan is None:
            tp_plan = "auto"

        # Not used anymore -- remove them from the kwargs
        for name in ["mirror", "_fast_init", "low_cpu_mem_usage", "from_tf", "from_flax", "offload_state_dict"]:
            _ = kwargs.pop(name, None)

        # For BC on torch_dtype argument
        if torch_dtype is not None:
            dtype = dtype if dtype is not None else torch_dtype
        if dtype is None:
            dtype = "auto"

        if is_offline_mode() and not local_files_only:
            local_files_only = True

        download_kwargs = {
            "cache_dir": cache_dir,
            "force_download": force_download,
            "proxies": proxies,
            "local_files_only": local_files_only,
            "token": token,
            "revision": revision,
            "subfolder": subfolder,
        }
        download_kwargs_with_commit = {**download_kwargs, "commit_hash": commit_hash}

        if state_dict is not None and (pretrained_model_name_or_path is not None or gguf_file is not None):
            raise ValueError(
                "`state_dict` cannot be passed together with a model name or a `gguf_file`. Use one of the two loading strategies."
            )

        if device_map == "auto" and int(os.environ.get("WORLD_SIZE", "0")):
            logger.info(
                "You've set device_map=`auto` while triggering a distributed run with torchrun. This might lead to unexpected behavior. "
                "If your plan is to load the model on each device, you should set device_map={"
                ": PartialState().process_index} where PartialState comes from accelerate library"
            )

        if tp_plan is not None or tp_size is not None:  # TP warnings, and setup
            device_map, device_mesh, tp_size = initialize_tensor_parallelism(
                tp_plan, tp_size=tp_size, device_mesh=device_mesh, device_map=device_map
            )

        if gguf_file is not None and not is_accelerate_available():
            raise ValueError("accelerate is required when loading a GGUF file `pip install accelerate`.")

        if adapter_kwargs is None:
            adapter_kwargs = {}

        _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
            pretrained_model_name_or_path,
            download_kwargs_with_commit,
            **adapter_kwargs,
        )
        device_map = check_and_set_device_map(device_map)  # warn, error and fix the device map

        user_agent = {"file_type": "model", "framework": "pytorch", "from_auto_class": from_auto_class}
        if from_pipeline is not None:
            user_agent["using_pipeline"] = from_pipeline

        # Load config if we don't provide a configuration
        if not isinstance(config, PreTrainedConfig):
            config_path = config if config is not None else pretrained_model_name_or_path
            config, model_kwargs = cls.config_class.from_pretrained(
                config_path,
                return_unused_kwargs=True,
                gguf_file=gguf_file,
                _from_auto=from_auto_class,
                _from_pipeline=from_pipeline,
                **download_kwargs,
                **kwargs,
            )
            if "gguf_file" in model_kwargs:
                model_kwargs.pop("gguf_file")
            commit_hash = model_kwargs.pop("_commit_hash", commit_hash)
        else:
            config = copy.deepcopy(config)
            model_kwargs = kwargs
            commit_hash = getattr(config, "_commit_hash", commit_hash)

        download_kwargs_with_commit["commit_hash"] = commit_hash

        # Because some composite configs call super().__init__ before instantiating the sub-configs, we need this call
        # to correctly redispatch recursively if the kwarg is provided
        if "attn_implementation" in kwargs:
            config._attn_implementation = kwargs.pop("attn_implementation")

        if "experts_implementation" in kwargs:
            config._experts_implementation = kwargs.pop("experts_implementation")

        hf_quantizer, config, device_map = get_hf_quantizer(
            config, quantization_config, device_map, weights_only, user_agent
        )

        if gguf_file:
            if hf_quantizer is not None:
                raise ValueError(
                    "You cannot combine Quantization and loading a model from a GGUF file, try again by making sure you did not passed a `quantization_config` or that you did not load a quantized model from the Hub."
                )
            if device_map is not None and (
                (isinstance(device_map, dict) and "disk" in device_map.values()) or "disk" in device_map
            ):
                raise RuntimeError(
                    "One or more modules is configured to be mapped to disk. Disk offload is not supported for models "
                    "loaded from GGUF files."
                )

        if kernel_config is not None and not use_kernels:
            logger.warning_once(
                "A kernel_config was provided but use_kernels is False; setting use_kernels=True automatically. To suppress this warning, explicitly set use_kernels to True."
            )
            use_kernels = True

        checkpoint_files, sharded_metadata = _get_resolved_checkpoint_files(
            pretrained_model_name_or_path=pretrained_model_name_or_path,
            variant=variant,
            gguf_file=gguf_file,
            use_safetensors=use_safetensors,
            download_kwargs=download_kwargs_with_commit,
            user_agent=user_agent,
            is_remote_code=cls.is_remote_code(),
            transformers_explicit_filename=getattr(config, "transformers_weights", None),
            tqdm_class=tqdm_class,
        )

        is_quantized = hf_quantizer is not None

        # Find the correct dtype based on current state
        config, dtype = _get_dtype(
            dtype, checkpoint_files, config, sharded_metadata, state_dict, weights_only, hf_quantizer
        )

        if gguf_file:
            from .modeling_gguf_pytorch_utils import load_gguf_checkpoint

            # we need a dummy model to get the state_dict - for this reason, we keep the state_dict as if it was
            # passed directly as a kwarg from now on
            with torch.device("meta"):
                dummy_model = cls(config)

            state_dict = load_gguf_checkpoint(
                checkpoint_files[0], return_tensors=True, model_to_load=dummy_model, torch_dtype=dtype
            )["tensors"]

        config.name_or_path = pretrained_model_name_or_path

        # Overwrite `config.fusion_config` if it is provided.
        if fusion_config is not None:
            config.fusion_config = copy.deepcopy(fusion_config)

        # Register fusion patches
        fusion_config = getattr(config, "fusion_config", None)
        if fusion_config is not None:
            from .fusion_mapping import register_fusion_patches

            register_fusion_patches(cls, config, fusion_config)

        model_init_context = cls.get_init_context(dtype, is_quantized, _is_ds_init_called, allow_all_kernels)

        config = copy.deepcopy(config)  # We do not want to modify the config inplace in from_pretrained.
        with ContextManagers(model_init_context):
            model = cls(config, *model_args, **model_kwargs)
            patch_output_recorders(model)

            if hf_quantizer is not None:  # replace module with quantized modules (does not touch weights)
                hf_quantizer.preprocess_model(
                    model=model,
                    dtype=dtype,
                    device_map=device_map,
                    checkpoint_files=checkpoint_files,
                    use_kernels=use_kernels,
                )

        # Create the dtype_plan to potentially use the `keep_in_fp32` flags (this needs to be called on the already
        # instantiated model, as the flags can be modified by instances sometimes)
        dtype_plan = model._get_dtype_plan(dtype)

        # Obtain the weight conversion mapping for this model if any are registered and apply to all submodels recursively
        weight_conversions = get_model_conversion_mapping(model, key_mapping, hf_quantizer)

        if _torch_distributed_available and device_mesh is not None:  # add hooks to nn.Modules: no weights
            model = distribute_model(model, tp_plan, distributed_config, device_mesh, tp_size)

        # Prepare the full device map
        if device_map is not None:
            device_map = _get_device_map(model, device_map, max_memory, hf_quantizer)

        # Finalize model weight initialization
        load_config = LoadStateDictConfig(
            pretrained_model_name_or_path=pretrained_model_name_or_path,
            ignore_mismatched_sizes=ignore_mismatched_sizes,
            sharded_metadata=sharded_metadata,
            device_map=device_map,
            disk_offload_folder=offload_folder,
            offload_buffers=offload_buffers,
            dtype=dtype,
            dtype_plan=dtype_plan,
            hf_quantizer=hf_quantizer,
            device_mesh=device_mesh,
            weights_only=weights_only,
            weight_mapping=weight_conversions,
            use_safetensors=use_safetensors,
            download_kwargs=download_kwargs,
            disable_mmap=disable_mmap,
        )
        loading_info, disk_offload_index = cls._load_pretrained_model(model, state_dict, checkpoint_files, load_config)
        loading_info = cls._finalize_model_loading(model, load_config, loading_info)
        model.eval()  # Set model in evaluation mode to deactivate Dropout modules by default
        model.set_use_kernels(use_kernels, kernel_config)

        # If it is a model with generation capabilities, attempt to load generation files (generation config,
        # custom generate function)
        if model.can_generate() and hasattr(model, "adjust_generation_fn") and not gguf_file:
            model.adjust_generation_fn(
                generation_config,
                from_auto_class,
                from_pipeline,
                pretrained_model_name_or_path,
                **download_kwargs,
                trust_remote_code=trust_remote_code,
                **kwargs,
            )

        # If the device_map has more than 1 device: dispatch model with hooks on all devices
        if device_map is not None and len(set(device_map.values())) > 1:
            accelerate_dispatch(model, hf_quantizer, device_map, offload_folder, disk_offload_index, offload_buffers)

        if hf_quantizer is not None:
            model.hf_quantizer = hf_quantizer
            hf_quantizer.postprocess_model(
                model
            )  # usually a no-op but sometimes needed, e.g to remove the quant config when dequantizing

        if _adapter_model_path is not None:
            if token is not None:
                adapter_kwargs["token"] = token
            loading_info = model.load_adapter(
                _adapter_model_path,
                adapter_name=adapter_name,
                load_config=load_config,
                adapter_kwargs=adapter_kwargs,
            )

        if output_loading_info:
            return model, loading_info.to_dict()
        return model