def load_model(
        self,
        *,
        # Local mode: pass a path to a .gguf file
        gguf_path: Optional[str] = None,
        # Vision projection (mmproj) for local vision models
        mmproj_path: Optional[str] = None,
        # HF mode: let llama-server download via -hf "repo:quant"
        hf_repo: Optional[str] = None,
        hf_variant: Optional[str] = None,
        hf_token: Optional[str] = None,
        # Common
        model_identifier: str,
        is_vision: bool = False,
        n_ctx: int = 4096,
        chat_template_override: Optional[str] = None,
        cache_type_kv: Optional[str] = None,
        speculative_type: Optional[str] = None,
        n_threads: Optional[int] = None,
        n_gpu_layers: Optional[int] = None,  # Accepted for caller compat, unused
        n_parallel: int = 1,
    ) -> bool:
        """
        Start llama-server with a GGUF model.

        Two modes:
        - Local: ``gguf_path="/path/to/model.gguf"`` → uses ``-m``
        - HF:    ``hf_repo="unsloth/gemma-3-4b-it-GGUF", hf_variant="Q4_K_M"`` → uses ``-hf``

        In HF mode, llama-server handles downloading, caching, and
        auto-loading mmproj files for vision models.

        Returns True if server started and health check passed.
        """
        self._cancel_event.clear()

        # ── Phase 1: kill old process (under lock, fast) ──────────
        with self._lock:
            self._kill_process()

        binary = self._find_llama_server_binary()
        if not binary:
            raise RuntimeError(
                "llama-server binary not found. "
                "Run setup.sh to build it, install llama.cpp, "
                "or set LLAMA_SERVER_PATH environment variable."
            )

        # ── Phase 2: download (NO lock held, so cancel can proceed) ──
        if hf_repo:
            model_path = self._download_gguf(
                hf_repo = hf_repo,
                hf_variant = hf_variant,
                hf_token = hf_token,
            )
            # Auto-download mmproj for vision models
            if is_vision and not mmproj_path:
                mmproj_path = self._download_mmproj(
                    hf_repo = hf_repo,
                    hf_token = hf_token,
                )
        elif gguf_path:
            if not Path(gguf_path).is_file():
                raise FileNotFoundError(f"GGUF file not found: {gguf_path}")
            model_path = gguf_path
        else:
            raise ValueError("Either gguf_path or hf_repo must be provided")

        # Set identifier early so _read_gguf_metadata can use it for DeepSeek detection
        self._model_identifier = model_identifier

        # Read GGUF metadata (context_length, chat_template) -- fast, header only
        self._read_gguf_metadata(model_path)

        # Check cancel after download
        if self._cancel_event.is_set():
            logger.info("Load cancelled after download phase")
            return False

        # ── Phase 3: start llama-server (under lock) ──────────────
        with self._lock:
            # Re-check cancel inside lock
            if self._cancel_event.is_set():
                logger.info("Load cancelled before server start")
                return False

            self._port = self._find_free_port()

            # Select GPU(s) based on model size + estimated KV cache.
            # Seed safe defaults before GPU probing so the except path
            # still has valid state to publish.
            effective_ctx = n_ctx if n_ctx > 0 else (self._context_length or 0)
            max_available_ctx = self._context_length or effective_ctx
            try:
                model_size = self._get_gguf_size_bytes(model_path)
                gpus = self._get_gpu_free_memory()

                # Resolve effective context: 0 means let llama-server use the
                # model's native length.  Only expand to a known native length
                # if metadata is available; otherwise preserve 0 as a sentinel.
                if n_ctx > 0:
                    effective_ctx = n_ctx
                elif self._context_length is not None:
                    effective_ctx = self._context_length
                else:
                    effective_ctx = 0
                original_ctx = effective_ctx
                # Default UI ceiling to the model's native context length.
                # GPU/VRAM-fit logic below may shrink this if hardware is limited.
                max_available_ctx = self._context_length or effective_ctx

                # Auto-cap context to fit in GPU VRAM and select GPUs.
                #
                # Two policies depending on whether the user set n_ctx:
                #
                # Explicit n_ctx (user chose a context length):
                #   Honor it. Try the full requested context with _select_gpus
                #   (which uses as many GPUs as needed). Only cap if it doesn't
                #   fit on any GPU combination.
                #
                # Auto n_ctx=0 (model's native context):
                #   Prefer fewer GPUs with reduced context over more GPUs,
                #   since multi-GPU is slower and the user didn't ask for a
                #   specific context length.
                gpu_indices, use_fit = None, True
                explicit_ctx = n_ctx > 0

                if gpus and self._can_estimate_kv() and effective_ctx > 0:
                    # Compute the largest hardware-aware cap from the model's
                    # native context across all usable GPU subsets (for UI
                    # bounds), independent of the currently requested context.
                    native_ctx_for_cap = self._context_length or effective_ctx
                    if native_ctx_for_cap > 0:
                        ranked_for_cap = sorted(gpus, key = lambda g: g[1], reverse = True)
                        best_cap = 0
                        for n_gpus in range(1, len(ranked_for_cap) + 1):
                            subset = ranked_for_cap[:n_gpus]
                            pool_mib = sum(free for _, free in subset)
                            capped = self._fit_context_to_vram(
                                native_ctx_for_cap,
                                pool_mib,
                                model_size,
                                cache_type_kv,
                            )
                            kv = self._estimate_kv_cache_bytes(capped, cache_type_kv)
                            total_mib = (model_size + kv) / (1024 * 1024)
                            if total_mib <= pool_mib * 0.90:
                                best_cap = max(best_cap, capped)
                        if best_cap > 0:
                            max_available_ctx = best_cap
                        else:
                            # Weights exceed 90% of every GPU subset's free
                            # memory, so there is no fitting context. Anchor
                            # the UI's "safe zone" threshold at 4096 (the
                            # spec's default when the model cannot fit) so
                            # the ctx slider shows the "might be slower"
                            # warning as soon as the user drags above the
                            # fallback default instead of never.
                            max_available_ctx = min(4096, native_ctx_for_cap)

                    if explicit_ctx:
                        # Honor the user's requested context verbatim. If it
                        # fits, pin GPUs and skip --fit; if it doesn't, ship
                        # -c <user_ctx> --fit on and let llama-server flex
                        # -ngl (CPU layer offload). The UI is expected to
                        # have surfaced the "might be slower" warning before
                        # the user submitted a ctx above the fit ceiling.
                        requested_total = model_size + self._estimate_kv_cache_bytes(
                            effective_ctx, cache_type_kv
                        )
                        gpu_indices, use_fit = self._select_gpus(requested_total, gpus)
                        # No silent shrink: effective_ctx stays == n_ctx.
                    else:
                        # Auto context: prefer fewer GPUs, cap context to fit.
                        ranked = sorted(gpus, key = lambda g: g[1], reverse = True)
                        for n_gpus in range(1, len(ranked) + 1):
                            subset = ranked[:n_gpus]
                            pool_mib = sum(free for _, free in subset)
                            capped = self._fit_context_to_vram(
                                effective_ctx,
                                pool_mib,
                                model_size,
                                cache_type_kv,
                            )
                            kv = self._estimate_kv_cache_bytes(capped, cache_type_kv)
                            total_mib = (model_size + kv) / (1024 * 1024)
                            if total_mib <= pool_mib * 0.90:
                                effective_ctx = capped
                                gpu_indices = sorted(idx for idx, _ in subset)
                                use_fit = False
                                break
                        else:
                            # No subset can host the weights (weights alone
                            # exceed 90% of every pool). Per spec, default
                            # the UI-visible context to 4096 and let
                            # --fit on flex -ngl so llama-server offloads
                            # layers to CPU RAM.
                            effective_ctx = min(4096, effective_ctx)

                elif gpus:
                    # Can't estimate KV -- fall back to file-size-only check.
                    # Without KV estimation we cannot prove a hardware cap, so
                    # keep the ceiling at the native context (already the default).
                    logger.debug(
                        "Falling back to file-size-only GPU selection",
                        model_size_gb = round(model_size / (1024**3), 2),
                    )
                    gpu_indices, use_fit = self._select_gpus(model_size, gpus)
                    if use_fit and not explicit_ctx:
                        # Weights don't fit on any subset. Default the UI to
                        # 4096 so the slider doesn't land on an unusable native
                        # context. --fit on will flex -ngl at runtime.
                        effective_ctx = (
                            min(4096, effective_ctx) if effective_ctx > 0 else 4096
                        )

                if effective_ctx < original_ctx:
                    kv_est = self._estimate_kv_cache_bytes(effective_ctx, cache_type_kv)
                    logger.info(
                        f"Context auto-reduced: {original_ctx} -> {effective_ctx} "
                        f"(model: {model_size / (1024**3):.1f} GB, "
                        f"est. KV cache: {kv_est / (1024**3):.1f} GB)"
                    )

                kv_cache_bytes = self._estimate_kv_cache_bytes(
                    effective_ctx, cache_type_kv
                )
                logger.info(
                    f"GGUF size: {model_size / (1024**3):.1f} GB, "
                    f"est. KV cache: {kv_cache_bytes / (1024**3):.1f} GB, "
                    f"context: {effective_ctx}, "
                    f"GPUs free: {gpus}, selected: {gpu_indices}, fit: {use_fit}"
                )
            except Exception as e:
                logger.warning(f"GPU selection failed ({e}), using --fit on")
                gpu_indices, use_fit = None, True
                effective_ctx = n_ctx  # fall back to original

            cmd = [
                binary,
                "-m",
                model_path,
                "--port",
                str(self._port),
                "-c",
                str(effective_ctx) if effective_ctx > 0 else "0",
                "--parallel",
                str(n_parallel),
                "--flash-attn",
                "on",  # Force flash attention for speed
                # Error out at n_ctx instead of silently rotating the KV cache; frontend catches it and points the user at "Context Length".
                "--no-context-shift",
            ]

            if use_fit:
                cmd.extend(["--fit", "on"])
            elif gpu_indices is not None:
                # Model fits on selected GPU(s) -- offload all layers
                cmd.extend(["-ngl", "-1"])

            if n_threads is not None:
                cmd.extend(["--threads", str(n_threads)])

            # Always enable Jinja chat template rendering for proper template support
            cmd.extend(["--jinja"])

            # KV cache data type
            _valid_cache_types = {
                "f16",
                "bf16",
                "q8_0",
                "q4_0",
                "q4_1",
                "q5_0",
                "q5_1",
                "iq4_nl",
                "f32",
            }
            if cache_type_kv and cache_type_kv in _valid_cache_types:
                cmd.extend(
                    ["--cache-type-k", cache_type_kv, "--cache-type-v", cache_type_kv]
                )
                self._cache_type_kv = cache_type_kv
                logger.info(f"KV cache type: {cache_type_kv}")
            else:
                self._cache_type_kv = None

            # Speculative decoding (n-gram self-speculation, zero VRAM cost)
            # ngram-mod: ~16 MB shared hash pool, constant memory/complexity,
            # variable draft lengths.  Helps most when the model repeats
            # existing text (code refactoring, summarization, reasoning).
            # For general chat with low repetition, overhead is ~5 ms.
            #
            # Benchmarks from llama.cpp PRs #18471, #19164:
            #   Scenario                        | Without | With    | Speedup
            #   gpt-oss-120b code refactor      | 181 t/s | 446 t/s | 2.5x
            #   Qwen3-235B offloaded            |  12 t/s |  21 t/s | 1.8x
            #   gpt-oss-120b repeat (92% accept)| 181 t/s | 814 t/s | 4.5x
            #
            # Params from llama.cpp docs (docs/speculative.md):
            #   --spec-ngram-size-n 24  (small n not recommended)
            #   --draft-min 48 --draft-max 64 (MoEs need long drafts;
            #     dense models can reduce these)
            # ref: https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md
            # ref: https://github.com/ggml-org/llama.cpp/pull/19164
            # ref: https://github.com/ggml-org/llama.cpp/pull/18471
            _valid_spec_types = {"ngram-simple", "ngram-mod"}
            if speculative_type and speculative_type in _valid_spec_types:
                if not is_vision:  # spec decoding disabled for vision models
                    cmd.extend(["--spec-type", speculative_type])
                    if speculative_type == "ngram-mod":
                        cmd.extend(
                            [
                                "--spec-ngram-size-n",
                                "24",
                                "--draft-min",
                                "48",
                                "--draft-max",
                                "64",
                            ]
                        )
                    self._speculative_type = speculative_type
                else:
                    self._speculative_type = None
            else:
                self._speculative_type = None

            # Apply custom chat template override if provided
            if chat_template_override:
                import tempfile

                self._chat_template_file = tempfile.NamedTemporaryFile(
                    mode = "w",
                    suffix = ".jinja",
                    delete = False,
                    prefix = "unsloth_chat_template_",
                )
                self._chat_template_file.write(chat_template_override)
                self._chat_template_file.close()
                cmd.extend(["--chat-template-file", self._chat_template_file.name])
                logger.info(
                    f"Using custom chat template file: {self._chat_template_file.name}"
                )

            # For reasoning models, set default thinking mode.
            # Qwen3.5/3.6 models below 9B (0.8B, 2B, 4B) disable thinking by default.
            # Only 9B and larger enable thinking.
            if self._supports_reasoning:
                thinking_default = True
                mid = (model_identifier or "").lower()
                if "qwen3.5" in mid or "qwen3.6" in mid:
                    size_val = _extract_model_size_b(mid)
                    if size_val is not None and size_val < 9:
                        thinking_default = False
                self._reasoning_default = thinking_default
                cmd.extend(
                    [
                        "--chat-template-kwargs",
                        json.dumps({"enable_thinking": thinking_default}),
                    ]
                )
                logger.info(
                    f"Reasoning model: enable_thinking={thinking_default} by default"
                )

            if mmproj_path:
                if not Path(mmproj_path).is_file():
                    logger.warning(f"mmproj file not found: {mmproj_path}")
                else:
                    cmd.extend(["--mmproj", mmproj_path])
                    logger.info(f"Using mmproj for vision: {mmproj_path}")

            # Option C: add --api-key for direct client access when enabled
            import os as _os
            import secrets as _secrets

            if _os.getenv("UNSLOTH_DIRECT_STREAM", "0") == "1":
                self._api_key = _secrets.token_urlsafe(32)
                cmd.extend(["--api-key", self._api_key])
                logger.info("llama-server started with --api-key for direct streaming")
            else:
                self._api_key = None

            _log_cmd = list(cmd)
            if "--api-key" in _log_cmd:
                _ki = _log_cmd.index("--api-key") + 1
                if _ki < len(_log_cmd):
                    _log_cmd[_ki] = "<redacted>"
            logger.info(f"Starting llama-server: {' '.join(_log_cmd)}")

            # Set library paths so llama-server can find its shared libs and CUDA DLLs
            import os
            import sys

            env = os.environ.copy()
            binary_dir = str(Path(binary).parent)

            if sys.platform == "win32":
                # On Windows, CUDA DLLs (cublas64_12.dll, cudart64_12.dll, etc.)
                # must be on PATH. Add CUDA_PATH\bin if available.
                path_dirs = [binary_dir]
                cuda_path = os.environ.get("CUDA_PATH", "")
                if cuda_path:
                    cuda_bin = os.path.join(cuda_path, "bin")
                    if os.path.isdir(cuda_bin):
                        path_dirs.append(cuda_bin)
                    # Some CUDA installs put DLLs in bin\x64
                    cuda_bin_x64 = os.path.join(cuda_path, "bin", "x64")
                    if os.path.isdir(cuda_bin_x64):
                        path_dirs.append(cuda_bin_x64)
                existing_path = env.get("PATH", "")
                env["PATH"] = ";".join(path_dirs) + ";" + existing_path
            else:
                # Linux: set LD_LIBRARY_PATH for shared libs next to the binary
                # and CUDA runtime libs (libcudart, libcublas, etc.)
                import platform

                lib_dirs = [binary_dir]
                _arch = platform.machine()  # x86_64, aarch64, etc.

                # Pip-installed nvidia CUDA runtime libs (e.g. torch's
                # bundled cuda-bindings).  The prebuilt llama.cpp binary
                # links against libcudart.so.13 / libcublas.so.13 which
                # live here, not in /usr/local/cuda.
                import glob as _glob

                for _nv_pattern in [
                    os.path.join(
                        sys.prefix,
                        "lib",
                        "python*",
                        "site-packages",
                        "nvidia",
                        "cu*",
                        "lib",
                    ),
                    os.path.join(
                        sys.prefix,
                        "lib",
                        "python*",
                        "site-packages",
                        "nvidia",
                        "cudnn",
                        "lib",
                    ),
                    os.path.join(
                        sys.prefix,
                        "lib",
                        "python*",
                        "site-packages",
                        "nvidia",
                        "nvjitlink",
                        "lib",
                    ),
                ]:
                    for _nv_dir in _glob.glob(_nv_pattern):
                        if os.path.isdir(_nv_dir):
                            lib_dirs.append(_nv_dir)

                for cuda_lib in [
                    "/usr/local/cuda/lib64",
                    f"/usr/local/cuda/targets/{_arch}-linux/lib",
                    # Fallback CUDA compat paths (e.g. binary built with
                    # CUDA 12 on a system where default /usr/local/cuda
                    # points to CUDA 13+).
                    "/usr/local/cuda-12/lib64",
                    "/usr/local/cuda-12.8/lib64",
                    f"/usr/local/cuda-12/targets/{_arch}-linux/lib",
                    f"/usr/local/cuda-12.8/targets/{_arch}-linux/lib",
                ]:
                    if os.path.isdir(cuda_lib):
                        lib_dirs.append(cuda_lib)
                existing_ld = env.get("LD_LIBRARY_PATH", "")
                new_ld = ":".join(lib_dirs)
                env["LD_LIBRARY_PATH"] = (
                    f"{new_ld}:{existing_ld}" if existing_ld else new_ld
                )

            # Pin to selected GPU(s) via CUDA_VISIBLE_DEVICES
            if gpu_indices is not None:
                env["CUDA_VISIBLE_DEVICES"] = ",".join(str(i) for i in gpu_indices)

            self._stdout_lines = []
            self._process = subprocess.Popen(
                cmd,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                text = True,
                env = env,
            )

            # Start background thread to drain stdout and prevent pipe deadlock
            self._stdout_thread = threading.Thread(
                target = self._drain_stdout, daemon = True, name = "llama-stdout"
            )
            self._stdout_thread.start()

            # Store the resolved on-disk path, not the caller's kwarg. In
            # HF mode the caller passes gguf_path=None and the real path
            # (``model_path``) is what llama-server is actually mmap'ing.
            # Downstream consumers (load_progress, log lines, etc.) need
            # the path that exists on disk.
            self._gguf_path = model_path
            self._hf_repo = hf_repo
            # For local GGUF files, extract variant from filename if not provided
            if hf_variant:
                self._hf_variant = hf_variant
            elif gguf_path:
                try:
                    from utils.models.model_config import _extract_quant_label

                    self._hf_variant = _extract_quant_label(gguf_path)
                except Exception:
                    self._hf_variant = None
            else:
                self._hf_variant = None
            self._is_vision = is_vision
            self._model_identifier = model_identifier

            # Store the effective (possibly capped) context separately.
            # Do NOT overwrite _context_length -- it holds the model's native
            # context length from GGUF metadata and is used for display/info.
            self._effective_context_length = (
                effective_ctx if effective_ctx > 0 else self._context_length
            )
            self._max_context_length = (
                max_available_ctx
                if max_available_ctx > 0
                else self._effective_context_length
            )

            # Wait for llama-server to become healthy
            if not self._wait_for_health(timeout = 600.0):
                self._kill_process()
                _gguf = gguf_path or ""
                _is_ollama = (
                    ".studio_links" in _gguf
                    or os.sep + "ollama_links" + os.sep in _gguf
                    or os.sep + ".cache" + os.sep + "ollama" + os.sep in _gguf
                    or (self._model_identifier or "").startswith("ollama/")
                )
                # Only show the Ollama-specific message when the server
                # output indicates a GGUF compatibility issue, not for
                # unrelated failures like OOM or missing binaries.
                if _is_ollama:
                    _output = "\n".join(self._stdout_lines[-50:]).lower()
                    _gguf_compat_hints = (
                        "key not found",
                        "unknown model architecture",
                        "failed to load model",
                    )
                    if any(h in _output for h in _gguf_compat_hints):
                        raise RuntimeError(
                            "Some Ollama models do not work with llama.cpp. "
                            "Try a different model, or use this model directly through Ollama instead."
                        )
                raise RuntimeError(
                    "llama-server failed to start. "
                    "Check that the GGUF file is valid and you have enough memory."
                )

            self._healthy = True

            logger.info(
                f"llama-server ready on port {self._port} "
                f"for model '{model_identifier}'"
            )
            return True