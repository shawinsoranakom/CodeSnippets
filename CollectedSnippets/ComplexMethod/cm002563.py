def _setup_devices(self) -> "torch.device":
        requires_backends(self, ["torch"])
        logger.info("PyTorch: setting up devices")
        if not is_sagemaker_mp_enabled():
            if not is_accelerate_available():
                raise ImportError(
                    f"Using the `Trainer` with `PyTorch` requires `accelerate>={ACCELERATE_MIN_VERSION}`: "
                    f"Please run `pip install transformers[torch]` or `pip install 'accelerate>={ACCELERATE_MIN_VERSION}'`"
                )
        # Build kwargs for PartialState; actual init happens below
        accelerator_state_kwargs: dict[str, Any] = {"enabled": True, "use_configured_state": False}
        if isinstance(self.accelerator_config, AcceleratorConfig):
            accelerator_state_kwargs["use_configured_state"] = self.accelerator_config.pop(
                "use_configured_state", False
            )
        if accelerator_state_kwargs["use_configured_state"]:
            if PartialState._shared_state == {}:
                raise ValueError(
                    "Passing `'use_configured_state':True` to the AcceleratorConfig requires a pre-configured "
                    "`AcceleratorState` or `PartialState` to be defined before calling `TrainingArguments`. "
                )
            self.distributed_state = PartialState(cpu=self.use_cpu)
            if self.deepspeed and self.distributed_state.distributed_type != DistributedType.DEEPSPEED:
                raise RuntimeError(
                    "Tried to use an already configured `Accelerator` or `PartialState` that was not initialized for DeepSpeed, "
                    "but also passed in a `deepspeed` configuration to the `TrainingArguments`. Please set "
                    "`use_configured_state:False` instead or setup your `Accelerator` or `PartialState` properly."
                )
        else:
            AcceleratorState._reset_state(reset_partial_state=True)
            self.distributed_state = None

        self._n_gpu = 1
        if self.use_cpu or strtobool(os.environ.get("ACCELERATE_USE_CPU", "False")):
            accelerator_state_kwargs["cpu"] = True
            accelerator_state_kwargs["backend"] = self.ddp_backend
            self._n_gpu = 0
        elif is_sagemaker_mp_enabled():
            accelerator_state_kwargs["enabled"] = False
            device = torch.device("cuda", smp.local_rank())
            torch.cuda.set_device(device)
        elif is_sagemaker_dp_enabled():
            accelerator_state_kwargs["_use_sagemaker_dp"] = True
        elif self.deepspeed:
            accelerator_state_kwargs["use_deepspeed"] = True
            accelerator_state_kwargs["timeout"] = timedelta(seconds=self.ddp_timeout)
        else:
            accelerator_state_kwargs["backend"] = self.ddp_backend
            accelerator_state_kwargs["timeout"] = timedelta(seconds=self.ddp_timeout)

        # Initialize PartialState with the accumulated kwargs
        if accelerator_state_kwargs.pop("enabled", False) and not accelerator_state_kwargs.pop(
            "use_configured_state", False
        ):
            # Temporarily set env var so Accelerate detects DeepSpeed
            use_deepspeed = accelerator_state_kwargs.pop("use_deepspeed", False)
            if use_deepspeed:
                os.environ["ACCELERATE_USE_DEEPSPEED"] = "true"
            self.distributed_state = PartialState(**accelerator_state_kwargs)
            if use_deepspeed:
                del os.environ["ACCELERATE_USE_DEEPSPEED"]
        if not is_sagemaker_mp_enabled():
            device = self.distributed_state.device
        if dist.is_available() and dist.is_initialized() and self.parallel_mode != ParallelMode.DISTRIBUTED:
            logger.warning(
                "torch.distributed process group is initialized, but parallel_mode != ParallelMode.DISTRIBUTED. "
                "In order to use Torch DDP, launch your script with `python -m torch.distributed.launch"
            )

        if is_torch_xla_available():
            device = self.distributed_state.device
            self._n_gpu = 0
        elif is_sagemaker_dp_enabled() or is_sagemaker_mp_enabled():
            pass  # _n_gpu already set above
        elif self.distributed_state.distributed_type == DistributedType.NO:
            if self.use_cpu:
                device = torch.device("cpu")
            elif is_torch_mps_available():
                device = torch.device("mps")
            elif is_torch_xpu_available():
                device = torch.device("xpu:0")
                torch.xpu.set_device(device)
            elif is_torch_mlu_available():
                device = torch.device("mlu:0")
                torch.mlu.set_device(device)
            elif is_torch_musa_available():
                device = torch.device("musa:0")
                torch.musa.set_device(device)
            elif is_torch_npu_available():
                device = torch.device("npu:0")
                torch.npu.set_device(device)
            elif is_torch_hpu_available():
                device = torch.device("hpu:0")
                torch.hpu.set_device(device)
            elif is_torch_neuron_available():
                device = torch.device("neuron:0")
                torch.neuron.set_device(device)
            else:
                # Default to cuda:0 (respects CUDA_VISIBLE_DEVICES); nn.DataParallel handles n_gpu > 1
                device = torch.device(
                    "cuda:0" if torch.cuda.is_available() else os.environ.get("ACCELERATE_TORCH_DEVICE", "cpu")
                )
                # _n_gpu may not have been set yet if _setup_devices is called early
                self._n_gpu = torch.cuda.device_count()
                if device.type == "cuda":
                    torch.cuda.set_device(device)
        return device