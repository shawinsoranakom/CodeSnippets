def from_model_id(
        cls,
        model_id: str,
        task: str,
        backend: str = "default",
        device: int | None = None,
        device_map: str | None = None,
        model_kwargs: dict | None = None,
        pipeline_kwargs: dict | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        **kwargs: Any,
    ) -> HuggingFacePipeline:
        """Construct the pipeline object from model_id and task."""
        try:
            from transformers import (  # type: ignore[import]
                AutoModelForCausalLM,
                AutoModelForSeq2SeqLM,
                AutoTokenizer,
            )
            from transformers import pipeline as hf_pipeline  # type: ignore[import]

        except ImportError as e:
            msg = (
                "Could not import transformers python package. "
                "Please install it with `pip install transformers`."
            )
            raise ValueError(msg) from e

        _model_kwargs = model_kwargs.copy() if model_kwargs else {}
        if device_map is not None:
            if device is not None:
                msg = (
                    "Both `device` and `device_map` are specified. "
                    "`device` will override `device_map`. "
                    "You will most likely encounter unexpected behavior."
                    "Please remove `device` and keep "
                    "`device_map`."
                )
                raise ValueError(msg)

            if "device_map" in _model_kwargs:
                msg = "`device_map` is already specified in `model_kwargs`."
                raise ValueError(msg)

            _model_kwargs["device_map"] = device_map
        tokenizer = AutoTokenizer.from_pretrained(model_id, **_model_kwargs)

        if backend in {"openvino", "ipex"}:
            if task not in VALID_TASKS:
                msg = (
                    f"Got invalid task {task}, "
                    f"currently only {VALID_TASKS} are supported"
                )
                raise ValueError(msg)

            err_msg = f"Backend: {backend} {IMPORT_ERROR.format(f'optimum[{backend}]')}"
            if not is_optimum_intel_available():
                raise ImportError(err_msg)

            # TODO: upgrade _MIN_OPTIMUM_VERSION to 1.22 after release
            min_optimum_version = (
                "1.22"
                if backend == "ipex" and task != "text-generation"
                else _MIN_OPTIMUM_VERSION
            )
            if is_optimum_intel_version("<", min_optimum_version):
                msg = (
                    f"Backend: {backend} requires optimum-intel>="
                    f"{min_optimum_version}. You can install it with pip: "
                    "`pip install --upgrade --upgrade-strategy eager "
                    f"`optimum[{backend}]`."
                )
                raise ImportError(msg)

            if backend == "openvino":
                if not is_openvino_available():
                    raise ImportError(err_msg)

                from optimum.intel import (  # type: ignore[import]
                    OVModelForCausalLM,
                    OVModelForSeq2SeqLM,
                )

                model_cls = (
                    OVModelForCausalLM
                    if task == "text-generation"
                    else OVModelForSeq2SeqLM
                )
            else:
                if not is_ipex_available():
                    raise ImportError(err_msg)

                if task == "text-generation":
                    from optimum.intel import (
                        IPEXModelForCausalLM,  # type: ignore[import]
                    )

                    model_cls = IPEXModelForCausalLM
                else:
                    from optimum.intel import (
                        IPEXModelForSeq2SeqLM,  # type: ignore[import]
                    )

                    model_cls = IPEXModelForSeq2SeqLM

        else:
            model_cls = (
                AutoModelForCausalLM
                if task == "text-generation"
                else AutoModelForSeq2SeqLM
            )

        model = model_cls.from_pretrained(model_id, **_model_kwargs)

        if tokenizer.pad_token is None:
            if model.config.pad_token_id is not None:
                tokenizer.pad_token_id = model.config.pad_token_id
            elif model.config.eos_token_id is not None and isinstance(
                model.config.eos_token_id, int
            ):
                tokenizer.pad_token_id = model.config.eos_token_id
            elif tokenizer.eos_token_id is not None:
                tokenizer.pad_token_id = tokenizer.eos_token_id
            else:
                tokenizer.add_special_tokens({"pad_token": "[PAD]"})

        if (
            (
                getattr(model, "is_loaded_in_4bit", False)
                or getattr(model, "is_loaded_in_8bit", False)
            )
            and device is not None
            and backend == "default"
        ):
            logger.warning(
                f"Setting the `device` argument to None from {device} to avoid "
                "the error caused by attempting to move the model that was already "
                "loaded on the GPU using the Accelerate module to the same or "
                "another device."
            )
            device = None

        if (
            device is not None
            and importlib.util.find_spec("torch") is not None
            and backend == "default"
        ):
            import torch

            cuda_device_count = torch.cuda.device_count()
            if device < -1 or (device >= cuda_device_count):
                msg = (
                    f"Got device=={device}, "
                    f"device is required to be within [-1, {cuda_device_count})"
                )
                raise ValueError(msg)
            if device_map is not None and device < 0:
                device = None
            if device is not None and device < 0 and cuda_device_count > 0:
                logger.warning(
                    "Device has %d GPUs available. "
                    "Provide device={deviceId} to `from_model_id` to use available"
                    "GPUs for execution. deviceId is -1 (default) for CPU and "
                    "can be a positive integer associated with CUDA device id.",
                    cuda_device_count,
                )
        if device is not None and device_map is not None and backend == "openvino":
            logger.warning("Please set device for OpenVINO through: `model_kwargs`")
        if "trust_remote_code" in _model_kwargs:
            _model_kwargs = {
                k: v for k, v in _model_kwargs.items() if k != "trust_remote_code"
            }
        _pipeline_kwargs = pipeline_kwargs or {}
        pipeline = hf_pipeline(  # type: ignore[call-overload]
            task=task,
            model=model,
            tokenizer=tokenizer,
            device=device,
            batch_size=batch_size,
            model_kwargs=_model_kwargs,
            **_pipeline_kwargs,
        )
        if pipeline.task not in VALID_TASKS:
            msg = (
                f"Got invalid task {pipeline.task}, "
                f"currently only {VALID_TASKS} are supported"
            )
            raise ValueError(msg)
        return cls(
            pipeline=pipeline,
            model_id=model_id,
            model_kwargs=_model_kwargs,
            pipeline_kwargs=_pipeline_kwargs,
            batch_size=batch_size,
            **kwargs,
        )