def _create_compile_meta(self, cfg: Config) -> dict[str, Any]:
        """
        Create compilation metadata for a given autotuner config. This involves
        processing the Config kwargs so that the kwargs that are not part
        of the triton signature are passed in as options to triton.compile
        instead
        """
        compile_meta = copy.deepcopy(self.triton_meta)
        compile_meta["num_warps"] = cfg.num_warps
        compile_meta["num_stages"] = cfg.num_stages

        cfg_kwargs = {**cfg.kwargs}
        if self.device_props.type == "hip":
            # `compile_meta["signature"]` contains the actual Triton kernel argument
            # names, including constexprs such as XBLOCK_0/XBLOCK_1 for combo kernels.
            # Any HIP config kwarg that is *not* in that signature is not a kernel
            # argument at all; it is a backend compile option that should be forwarded
            # to triton.compile via `options`, not materialized as a constexpr.
            signature_arg_names = OrderedSet(compile_meta["signature"])
            backend_options = {
                key: value
                for key, value in cfg_kwargs.items()
                if key not in signature_arg_names
            }
            cfg_kwargs = {
                key: value
                for key, value in cfg_kwargs.items()
                if key in signature_arg_names
            }
            if backend_options:
                # Stash backend-only options separately so they do not get mixed into
                # `constants`, which are interpreted as signature-bound constexpr args.
                compile_meta["backend_options"] = backend_options
        compile_meta["constants"].update(cfg_kwargs)

        for i in get_constexprs(self.fn):
            arg_name = self.fn.arg_names[i]
            if arg_name not in compile_meta["constants"] and (
                arg_name == "num_warps" or arg_name == "num_stages"
            ):
                compile_meta["constants"][arg_name] = getattr(cfg, arg_name)
        if HAS_WARP_SPEC:
            compile_meta["num_consumer_groups"] = getattr(cfg, "num_consumer_groups", 0)
            compile_meta["num_buffers_warp_spec"] = getattr(
                cfg, "num_buffers_warp_spec", 0
            )

        compile_meta["debug"] = self.inductor_meta.get(
            "assert_indirect_indexing", True
        ) and not self.inductor_meta.get("is_hip", False)

        # device type will be "hip" rather than "cuda" here
        compile_meta["device_type"] = self.device_props.type
        compile_meta["cc"] = self.device_props.cc

        for k in tlx_only_cuda_options():
            if v := getattr(cfg, k, None):
                compile_meta[k] = v

        return compile_meta