def dep_fn(self, *args, **kwargs):
            size_bytes: int = size(self, *args, **kwargs) if callable(size) else size
            _device = device
            if _device is None:
                if hasattr(self, "get_primary_device"):
                    _device = self.get_primary_device()
                else:
                    _device = self.device

            # If this is running with GPU cpp_wrapper, the autotuning step will generate
            # an additional array of the same size as the input.
            if inductor and torch._inductor.config.cpp_wrapper and _device != "cpu":
                size_bytes *= 2
            if not _has_sufficient_memory(_device, size_bytes):
                raise unittest.SkipTest(f"Insufficient {_device} memory")

            return fn(self, *args, **kwargs)