def __init__(
        self,
        model: str,
        vllm_serve_args: list[str],
        *,
        env_dict: dict[str, str] | None = None,
        seed: int = 0,
        auto_port: bool = True,
        max_wait_seconds: float | None = None,
        override_hf_configs: dict[str, Any] | None = None,
    ) -> None:
        if auto_port:
            if "-p" in vllm_serve_args or "--port" in vllm_serve_args:
                raise ValueError(
                    "You have manually specified the port when `auto_port=True`."
                )

            # No need for a port if using unix sockets
            if "--uds" not in vllm_serve_args:
                # Don't mutate the input args
                vllm_serve_args = vllm_serve_args + ["--port", str(get_open_port())]
        if seed is not None:
            if "--seed" in vllm_serve_args:
                raise ValueError(
                    f"You have manually specified the seed when `seed={seed}`."
                )

            vllm_serve_args = vllm_serve_args + ["--seed", str(seed)]

        if override_hf_configs is not None:
            vllm_serve_args = vllm_serve_args + [
                "--hf-overrides",
                json.dumps(override_hf_configs),
            ]

        parser = FlexibleArgumentParser(description="vLLM's remote server.")
        subparsers = parser.add_subparsers(required=False, dest="subparser")
        parser = self._create_cli_subcommand().subparser_init(subparsers)
        args = parser.parse_args(["--model", model, *vllm_serve_args])
        self.uds = args.uds
        if args.uds:
            self.host = None
            self.port = None
        else:
            self.host = str(args.host or "127.0.0.1")
            self.port = int(args.port)

        self.show_hidden_metrics = (
            getattr(args, "show_hidden_metrics_for_version", None) is not None
        )

        self._pre_download_model(model, args)

        # Record GPU memory before server start so we know what
        # "released" looks like.
        self._pre_server_gpu_memory = self._get_gpu_memory_used()
        if self._pre_server_gpu_memory is not None:
            pre_gb = self._pre_server_gpu_memory / 1e9
            print(
                f"[{type(self).__name__}] GPU memory before server start: "
                f"{pre_gb:.2f} GB"
            )

        self._start_server(model, vllm_serve_args, env_dict)
        max_wait_seconds = max_wait_seconds or 480
        try:
            self._wait_for_server(url=self.url_for("health"), timeout=max_wait_seconds)
        except Exception:
            # If the server never became healthy, we must still clean up
            # the subprocess tree. Without this, a timeout in __init__
            # leaks the server + EngineCore processes (and their GPU
            # memory), because __exit__ is never called when __init__
            # raises inside a ``with`` statement.
            self._shutdown()
            raise