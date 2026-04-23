def __init__(
        self,
        model_name = "unsloth/Llama-3.1-8B-Instruct-unsloth-bnb-4bit",
        max_seq_length = 2048,
        gpu_memory_utilization = 0.98,
        float8_kv_cache = False,
        conservativeness = 1.0,
        token = None,
        timeout = 1200,  # maybe this is not enough for large models if we need to download
        **kwargs,
    ):
        assert type(model_name) is str
        assert type(max_seq_length) is int
        assert type(gpu_memory_utilization) is float
        assert type(float8_kv_cache) is bool
        assert type(conservativeness) is float
        assert token is None or type(token) is str

        self.model_name = model_name
        self.max_seq_length = max_seq_length

        from transformers import AutoConfig, AutoTokenizer

        self.config = AutoConfig.from_pretrained(
            model_name,
            token = token,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            token = token,
        )
        load_vllm, patch_vllm, delete_vllm = _load_vllm_utils()
        self._delete_vllm = delete_vllm
        patch_vllm(debug = False)
        engine_args = load_vllm(
            model_name = model_name,
            config = self.config,
            gpu_memory_utilization = gpu_memory_utilization,
            max_seq_length = max_seq_length,
            disable_log_stats = True,
            float8_kv_cache = float8_kv_cache,
            conservativeness = conservativeness,
            return_args = True,
            enable_lora = False,
            use_bitsandbytes = False,
            compilation_config = 3,
            **kwargs,
        )
        if "dtype" in engine_args:
            dtype_val = engine_args["dtype"]
            if dtype_val == torch.float16:
                dtype_val = "float16"
            elif dtype_val == torch.bfloat16:
                dtype_val = "bfloat16"
            elif dtype_val == torch.float32:
                dtype_val = "float32"
            engine_args["dtype"] = dtype_val
            # Convert torch.bfloat16, torch.float16, etc. to valid CLI string
            if hasattr(dtype_val, "name"):
                engine_args["dtype"] = dtype_val.name
            elif isinstance(dtype_val, str) and dtype_val.startswith("torch."):
                engine_args["dtype"] = dtype_val.split(".")[-1]
            # Only allow valid vLLM choices
            valid_dtypes = {"auto", "bfloat16", "float", "float16", "float32", "half"}
            if engine_args["dtype"] not in valid_dtypes:
                engine_args["dtype"] = "auto"
        if "device" in engine_args:
            del engine_args["device"]
        if "model" in engine_args:
            del engine_args["model"]

        subprocess_commands = [
            "vllm",
            "serve",
            str(model_name),
        ]
        for key, value in engine_args.items():
            flag = key.replace("_", "-")
            if key == "compilation_config":
                # [TODO] Unsure why subprocess doesn't process json properly
                # Also -O3 breaks on T4!
                # subprocess_commands += ["-O3",]
                continue
            which = str(value).replace("torch.", "")
            if which == "True":
                # Ignore --enforce-eager True
                subprocess_commands += [
                    "--" + flag,
                ]
            elif which == "False":
                # Ignore flag
                pass
            elif which == "None":
                # Ignore flag
                pass
            else:
                subprocess_commands += [
                    "--" + flag,
                    which,
                ]
        logger.info(subprocess_commands)
        vllm_process = subprocess.Popen(
            subprocess_commands,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            start_new_session = True,
        )
        ready_re = re.compile(r"Starting vLLM API server(?:\s+\d+)?\s+on\b")
        self.vllm_process = vllm_process
        self.stdout_capture = PipeCapture(
            vllm_process.stdout,
            keep_lines = 1000,
            echo = True,
            name = "vLLM STDOUT",
            ready_regex = ready_re,
            text = False,
        )
        self.stderr_capture = PipeCapture(
            vllm_process.stderr,
            keep_lines = 2000,
            echo = False,
            name = "vLLM STDERR",
            ready_regex = None,
            text = False,
        )
        # we don't print stderr to console but self.stderr_capture.tail(200) will print the last 200 lines

        ready = self.stdout_capture.wait_for_ready(timeout = timeout)
        if not ready:
            if self.stdout_capture.has_closed() or self.vllm_process.poll() is not None:
                print("Stdout stream ended before readiness message detected.")
                print("\n--- stdout tail ---\n", self.stdout_capture.tail(50))
                print("\n--- stderr tail ---\n", self.stderr_capture.tail(50))
            else:
                print(f"Unsloth: vllm_process failed to load! (timeout={timeout})")
                print("\n--- stdout tail ---\n", self.stdout_capture.tail(50))
                print("\n--- stderr tail ---\n", self.stderr_capture.tail(50))
            terminate_tree(self.vllm_process)
            return
        else:
            print("vLLM Server Ready Detected")

        trial = 0
        while not self.check_vllm_status():
            if trial >= 100:
                print("Unsloth: vllm_process failed to load!")
                print("\n--- stdout tail ---\n", self.stdout_capture.tail(50))
                print("\n--- stderr tail ---\n", self.stderr_capture.tail(50))
                terminate_tree(self.vllm_process)
                return
            trial += 1
            time.sleep(1)
        return