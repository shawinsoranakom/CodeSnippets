def _create_compile_options(
        self, cfg: Config, compile_meta: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create options to pass to triton.compile based on the compile metadata
        and the given config.
        """
        options = {
            "num_warps": compile_meta["num_warps"],
            "num_stages": compile_meta["num_stages"],
            "debug": compile_meta["debug"],
            "sanitize_overflow": False,  # turn off additional asserts added for overflow checks
        }
        if "enable_fp_fusion" in compile_meta:
            options["enable_fp_fusion"] = compile_meta["enable_fp_fusion"]
        if HAS_WARP_SPEC:
            options.update(
                {
                    "num_consumer_groups": compile_meta.get("num_consumer_groups", 0),
                    "num_buffers_warp_spec": compile_meta.get(
                        "num_buffers_warp_spec", 0
                    ),
                }
            )
        if self.device_props.type == "cuda":
            options.update(
                {
                    "launch_cooperative_grid": compile_meta.get(
                        "launch_cooperative_grid", False
                    ),
                    "launch_pdl": compile_meta.get("launch_pdl", False),  # True
                }
            )
            if compile_meta.get("disable_ftz", False):
                options["enable_reflect_ftz"] = False
            for k in tlx_only_cuda_options():
                if v := getattr(cfg, k, None):
                    options[k] = v
        if self.device_props.type == "hip":
            # HIP backend options are consumed by Triton out-of-band from the kernel
            # signature. They are intentionally *not* present in `constants`.
            options.update(compile_meta.get("backend_options", {}))

        if self.device_props.type == "xpu" and XPU_KERNEL_FORMAT == "zebin":
            options["generate_native_code"] = True

        return options