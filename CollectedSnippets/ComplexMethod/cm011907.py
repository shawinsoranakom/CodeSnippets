def jit_lines(self):
        if self.use_jit:
            return "@triton.jit"

        argdefs, _, signature, _ = self.args.python_argdefs()
        triton_meta: dict[str, Any] = {
            "signature": signature_to_meta(
                signature,
                size_dtype=self.index_dtype,
                argdefs=argdefs,
                is_template=True,
            ),
            "device": DeviceProperties.create(self.output_node.get_device()),
            "constants": {},
        }
        triton_meta["configs"] = [config_of(signature)]
        for arg_num in equal_1_arg_indices(signature):  # type: ignore[index]
            triton_meta["constants"][signature[arg_num].name] = 1  # type: ignore[index,union-attr]
        matrix_instr_nonkdim = self.meta.get("matrix_instr_nonkdim", None)
        waves_per_eu = self.meta.get("waves_per_eu", None)
        kpack = self.meta.get("kpack", None)
        if matrix_instr_nonkdim:
            triton_meta["matrix_instr_nonkdim"] = matrix_instr_nonkdim
        if waves_per_eu:
            triton_meta["waves_per_eu"] = waves_per_eu
        if kpack:
            triton_meta["kpack"] = kpack

        for k in tlx_only_cuda_options():
            if v := self.meta.get(k, None):
                triton_meta[k] = v

        if self.triton_meta is None:
            self.triton_meta = triton_meta
        else:
            self.triton_meta.update(triton_meta)

        inductor_meta = {
            "kernel_name": str(Placeholder.DESCRIPTIVE_NAME),
            **self.inductor_meta_common(),
            **FixedGrid.setup_grid_as_args(),
        }
        if config.profile_bandwidth or config.benchmark_kernel:
            num_gb = self.estimate_kernel_num_bytes() / 1e9
            inductor_meta["kernel_num_gb"] = num_gb
        if config.benchmark_kernel:
            flops = self.estimate_flops()
            inductor_meta["kernel_flop"] = flops

        inductor_meta["config_args"] = self.meta

        template_args = f"""
            num_stages={self.num_stages},
            num_warps={self.num_warps},
            triton_meta={self.triton_meta!r},
            inductor_meta={inductor_meta!r},
        """

        if HAS_WARP_SPEC:
            template_args += f"""
            num_consumer_groups={self.num_consumer_groups},
            num_buffers_warp_spec={self.num_buffers_warp_spec},
        """

        for k in tlx_only_cuda_options():
            if v := self.meta.get(k, None):
                template_args += f"""
                    {k}={v},
                """
                self.triton_meta[k] = v

        return f"""
            @triton_heuristics.template(
                {template_args}
            )
            @triton.jit
        """