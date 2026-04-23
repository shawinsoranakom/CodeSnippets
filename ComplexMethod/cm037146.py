def _report_usage_once(
        self,
        model_architecture: str,
        usage_context: UsageContext,
        extra_kvs: dict[str, Any],
    ) -> None:
        # Platform information
        from vllm.platforms import current_platform

        if current_platform.is_cuda_alike():
            self.gpu_count = current_platform.device_count()
            self.gpu_type, self.gpu_memory_per_device = cuda_get_device_properties(
                0, ("name", "total_memory")
            )
        if current_platform.is_cuda():
            self.cuda_runtime = torch.version.cuda
        if current_platform.is_xpu():
            self.xpu_runtime = torch.version.xpu
            self.gpu_count = torch.xpu.device_count()
            self.gpu_type = torch.xpu.get_device_name(0)
            self.gpu_memory_per_device = torch.xpu.get_device_properties(0).total_memory
        if current_platform.is_tpu():  # noqa: SIM102
            if not self._report_tpu_inference_usage():
                logger.exception("Failed to collect TPU information")
        self.provider = _detect_cloud_provider()
        self.architecture = platform.machine()
        self.platform = platform.platform()
        self.total_memory = psutil.virtual_memory().total

        info = cpuinfo.get_cpu_info()
        self.num_cpu = info.get("count", None)
        self.cpu_type = info.get("brand_raw", "")
        self.cpu_family_model_stepping = ",".join(
            [
                str(info.get("family", "")),
                str(info.get("model", "")),
                str(info.get("stepping", "")),
            ]
        )

        # vLLM information
        self.context = usage_context.value
        self.vllm_version = VLLM_VERSION
        self.model_architecture = model_architecture

        # Environment variables
        self.env_var_json = json.dumps(
            {env_var: getattr(envs, env_var) for env_var in _USAGE_ENV_VARS_TO_COLLECT}
        )

        # Metadata
        self.log_time = _get_current_timestamp_ns()
        self.source = envs.VLLM_USAGE_SOURCE

        data = vars(self)
        if extra_kvs:
            data.update(extra_kvs)

        self._write_to_file(data)
        self._send_to_server(data)