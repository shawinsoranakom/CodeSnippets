def _run_op(self, op, mps_sample, dtype=None):
        # MPS uses float32 intermediates for these ops, so the CPU reference
        # must also run in float32 to avoid comparing against less-precise
        # native half-precision CPU results.
        if op.name in ["grid_sampler_2d", "grid_sampler_3d"] and dtype is None and mps_sample.input.dtype in [torch.float16, torch.bfloat16]:
            dtype = torch.float32

        cpu_sample = transform_opinfo_sample_to_cpu(mps_sample, dtype)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            mps_out = op(mps_sample.input, *mps_sample.args, **mps_sample.kwargs)
            try:
                cpu_out = op(cpu_sample.input, *cpu_sample.args, **cpu_sample.kwargs)
            except NotImplementedError:
                # TODO: Handle list inputs later
                if not isinstance(mps_out, torch.Tensor):
                    raise
                if mps_sample.input.dtype in [torch.float16, torch.bfloat16]:
                    dtype = torch.float32
                elif mps_sample.input.dtype == torch.bool:
                    dtype = torch.uint8

                # Often CPU ops are not implemented for low precision dtypes
                # In that case, upcast to higher precision and try again
                cpu_sample = transform_opinfo_sample_to_cpu(mps_sample, dtype=torch.float32)
                cpu_out = op(cpu_sample.input, *cpu_sample.args, **cpu_sample.kwargs)

        if dtype is not None:
            cpu_out = cpu_out.to(dtype=mps_out.dtype)

        return mps_out, cpu_out, cpu_sample