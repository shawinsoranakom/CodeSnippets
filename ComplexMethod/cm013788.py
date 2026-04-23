def start_trace(self) -> None:
        if self.execution_trace_observer:
            self.execution_trace_observer.start()
        if self.profiler is None:
            raise AssertionError("Profiler must be initialized before starting trace")
        self.profiler._start_trace()

        if self.profile_memory:
            self.add_metadata_json("profile_memory", "1")
        if self.with_stack:
            self.add_metadata_json("with_stack", "1")
        if self.record_shapes:
            self.add_metadata_json("record_shapes", "1")
        if self.with_modules:
            self.add_metadata_json("with_modules", "1")
        if self.with_flops:
            self.add_metadata_json("with_flops", "1")

        if kineto_available():
            dist_info = self._get_distributed_info()
            if dist_info:
                self.add_metadata_json(
                    "distributedInfo", json.dumps(dist_info, cls=_NumpyEncoder)
                )

            cuda_version = None
            if hasattr(torch, "version"):
                from torch.torch_version import TorchVersion

                cuda_version = TorchVersion(getattr(torch.version, "cuda", "0.0"))

            if self.has_cudagraphs and (
                (cuda_version and cuda_version < "12.6")
                or not profiler_allow_cudagraph_cupti_lazy_reinit_cuda12()
            ):
                os.environ["DISABLE_CUPTI_LAZY_REINIT"] = "1"
                self.add_metadata_json("DISABLE_CUPTI_LAZY_REINIT", "1")
                # FIXME: CUDA Graph does not work well with CUPTI teardown.
                #   1) crashes on 1st lazy CUPTI re-init after teardown (CUDA 11)
                #   2) crashes on 2nd non-lazy CUPTI re-init after teardown (CUDA 12)
                # Workaround: turn off CUPTI teardown when using CUDA Graphs.
                os.environ["TEARDOWN_CUPTI"] = "0"

            # Insert the preset user metadata to the trace
            for k, v in self.preset_metadata.items():
                self.add_metadata_json(k, v)