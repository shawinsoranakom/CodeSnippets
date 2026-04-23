def _precompile_config(self, cfg: Config) -> CompileResult[_KernelType]:
        """Ahead of time compile a given autotuner config."""
        compile_meta = self._create_compile_meta(cfg)

        if self.device_props.type == "cpu":
            triton_helpers.set_driver_to_cpu()
        else:
            triton_helpers.set_driver_to_gpu()

        if not ASTSource:
            raise RuntimeError("Installed triton version too old, please upgrade")

        compile_args = (
            ASTSource(
                self.fn,
                compile_meta["signature"],
                compile_meta["constants"],
                compile_meta["configs"][0],
            ),
        )

        if self.device_props.type == "mtia":
            from mtia.host_runtime.torch_mtia.acc_flags import (  # type: ignore[import-not-found]
                build_codename,
            )

            arch = build_codename()
        else:
            arch = compile_meta["cc"]

        target = GPUTarget(
            compile_meta["device_type"],
            arch,
            cc_warp_size(compile_meta["cc"]),
        )

        options = self._create_compile_options(cfg, compile_meta)

        compile_kwargs = {
            "target": target,
            "options": options,
        }

        try:
            binary = triton.compile(*compile_args, **compile_kwargs)
        except Exception:
            log.exception(
                "Triton compilation failed: %s\n%s\nmetadata: %s",
                self.inductor_meta.get("kernel_name", "triton_"),
                self.fn.src,
                compile_meta,
            )
            raise

        # Simulate JIT Hook call
        if (
            torch._inductor.config.run_jit_post_compile_hook
            and knobs
            and getattr(knobs.runtime, "jit_post_compile_hook", None)
        ):
            try:
                hook = knobs.runtime.jit_post_compile_hook

                # base args everyone should get
                call_kwargs = dict(
                    key=getattr(self.fn, "cache_key", self.kernel_hash or str(self.fn)),
                    repr=getattr(self.fn, "src", None),
                    fn=self.fn,
                    compile=binary,
                    is_manual_warmup=False,
                    already_compiled=True,
                )

                # only add inductor_args if the hook takes it
                sig = inspect.signature(hook)
                params = sig.parameters
                if "inductor_args" in params and "config_args" in self.inductor_meta:
                    call_kwargs["inductor_args"] = self.inductor_meta["config_args"]

                hook(**call_kwargs)
            except Exception:
                log.exception("jit_post_compile_hook failed")

        TritonBundler.put(
            triton_hash_to_path_key(binary.hash), self.triton_meta.get("device", 0)
        )
        # If the binary has a cubin file to directly launch, save it on the binary
        static_launcher = StaticTritonCompileResult.can_statically_launch(
            binary, self.inductor_meta, self.triton_meta, self.heuristic_type
        )

        if static_launcher is not None:
            result = StaticTritonCompileResult(
                static_launcher, cfg, compile_meta, self.inductor_meta
            )
            return result

        return TritonCompileResult(binary, cfg, compile_meta, self.inductor_meta)