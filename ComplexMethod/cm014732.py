def test_batchnorm(self, dims, mode, memory_format, ref_backend, mixed, dtype):
        if torch.version.cuda:
            if self._testMethodName in ("test_batchnorm_2D_train_NCHW_vs_cpu_mixed_bfloat16",
                                        "test_batchnorm_3D_train_NCHW_vs_cpu_mixed_bfloat16",
                                        "test_batchnorm_2D_train_NHWC_vs_NCHW_mixed_bfloat16",
                                        "test_batchnorm_3D_train_NHWC_vs_NCHW_mixed_bfloat16",
                                        "test_batchnorm_3D_train_NCHW_vs_native_mixed_float16"):
                self.skipTest("Failed on CUDA")

        if torch.version.hip:
            if self._testMethodName in ("test_batchnorm_2D_train_NCHW_vs_native_mixed_bfloat16",
                                        "test_batchnorm_3D_train_NCHW_vs_native_mixed_bfloat16") \
                    and _get_torch_rocm_version() >= (6, 4):
                # https://github.com/pytorch/pytorch/issues/156513
                self.skipTest("bfloat16 NCHW train failed due to native tolerance issue")

            if self._testMethodName == "test_batchnorm_3D_train_NCHW_vs_native_mixed_float16":
                self.skipTest("3D float16 NCHW train failed on ROCm")

        if dims == 3 and memory_format in ("NHWC", "NCHW"):
            memory_format = memory_format + "3D"

        def _create_tensor(size, memory_format, dtype, device):
            t = torch.empty(size=size, memory_format=memory_format, dtype=dtype, device=device)
            t = t.random_(1, 10)
            return t

        def _get_ref_device(backend: str , device: str):
            # If 'backend' specifies the memory format, return 'device' arg, otherwise return a device matches the backend
            if backend in ("NHWC", "NHWC3D", "NCHW", "NCHW3D"):
                return device
            if backend == "native":
                return "cuda"
            if backend == "cpu":
                return "cpu"
            else:
                raise ValueError("Unknown backend")

        def _get_backend_memory_format(backend: str, memory_format: torch.memory_format) -> torch.memory_format:
            # If 'backend' specifies the memory format, return it, otherwise look at 'memory_format' arg
            if backend == "NHWC":
                return torch.channels_last
            if backend == "NHWC3D":
                return torch.channels_last_3d
            if backend in ("NCHW", "NCHW3D"):
                return torch.contiguous_format
            if memory_format in (torch.contiguous_format, torch.channels_last, torch.channels_last_3d):
                return memory_format
            raise ValueError(f"Unable to detect memory format for backend={backend} and memory_format={memory_format}")

        def _get_memory_format(t: torch.Tensor) -> torch.memory_format:
            if t.is_contiguous(memory_format=torch.contiguous_format):
                return torch.contiguous_format
            if t.is_contiguous(memory_format=torch.channels_last):
                return torch.channels_last
            if t.is_contiguous(memory_format=torch.channels_last_3d):
                return torch.channels_last_3d
            return ValueError("Unsupported memory_format")

        def _get_memory_format_from_name(memory_format_name: str) -> torch.memory_format:
            if memory_format_name == "NHWC":
                return torch.channels_last
            elif memory_format_name == "NHWC3D":
                return torch.channels_last_3d
            elif memory_format_name in ("NCHW", "NCHW3D"):
                return torch.contiguous_format
            return ValueError("Unsupported memory_format")

        def _create_backend(inp: torch.Tensor, mixed: bool = False):
            if inp.dim() == 4:
                return nn.BatchNorm2d(inp.size(1), device=inp.device, dtype=torch.float if mixed else inp.dtype)
            else:
                return nn.BatchNorm3d(inp.size(1), device=inp.device, dtype=torch.float if mixed else inp.dtype)

        def _test_batchnorm_train(inp, grad, mixed, ref_inp, ref_grad, ref_backend):
            mod = _create_backend(inp, mixed).train()
            mod.weight.data.uniform_()
            mod.bias.data.uniform_()

            ref_mod = _create_backend(ref_inp, mixed).train()
            ref_mod.load_state_dict(mod.state_dict())

            out = mod(inp)
            out.backward(grad)

            with torch.backends.cudnn.flags(enabled=False) if ref_backend == "native" else contextlib.nullcontext():
                ref_out = ref_mod(ref_inp)
                ref_out.backward(ref_grad)

            self.assertTrue(out.is_contiguous(memory_format=_get_memory_format(inp)))
            self.assertTrue(ref_out.is_contiguous(memory_format=_get_memory_format(ref_inp)))
            self.assertEqual(out, ref_out)
            self.assertEqual(mod.weight.grad, ref_mod.weight.grad)
            self.assertEqual(mod.bias.grad, ref_mod.bias.grad)
            self.assertEqual(mod.running_mean, ref_mod.running_mean)
            self.assertEqual(mod.running_var, ref_mod.running_var)
            self.assertEqual(inp.grad, ref_inp.grad)

        def _train(memory_format_name, ref_backend, mixed, dtype):
            memory_format = _get_memory_format_from_name(memory_format_name)

            ref_memory_format = _get_backend_memory_format(ref_backend, memory_format)
            ref_device = _get_ref_device(ref_backend, device="cuda")

            size = (4, 8, 2, 2, 2) if memory_format_name in ("NCHW3D", "NHWC3D") else (4, 8, 2, 2)
            inp = _create_tensor(size, memory_format, dtype, device="cuda").detach().requires_grad_()
            grad = _create_tensor(size, memory_format, dtype, device="cuda")
            ref_inp = inp.detach().clone(memory_format=ref_memory_format).to(device=ref_device).requires_grad_()
            ref_grad = grad.detach().clone(memory_format=ref_memory_format).to(device=ref_device)

            _test_batchnorm_train(inp=inp, grad=grad, mixed=mixed,
                                  ref_inp=ref_inp, ref_grad=ref_grad, ref_backend=ref_backend)

        def _inference(memory_format_name, ref_backend, mixed, dtype):
            memory_format = _get_memory_format_from_name(memory_format_name)
            ref_memory_format = _get_backend_memory_format(ref_backend, memory_format)
            ref_device = _get_ref_device(ref_backend, device="cuda")

            size = (2, 64, 50, 50, 50) if memory_format_name in ("NCHW3D", "NHWC3D") else (2, 64, 50, 50)
            inp = _create_tensor(size, memory_format, dtype, device="cuda")
            ref_inp = inp.detach().clone(memory_format=ref_memory_format).to(device=ref_device)
            mod = _create_backend(inp, mixed).eval()
            ref_mod = _create_backend(ref_inp, mixed).eval()

            out = mod(inp)
            with torch.backends.cudnn.flags(enabled=False) if ref_backend == "native" else contextlib.nullcontext():
                ref_out = ref_mod(ref_inp)
            self.assertEqual(out, ref_out)

        if mode == "train":
            _train(memory_format, ref_backend, mixed, dtype)
        else:
            _inference(memory_format, ref_backend, mixed, dtype)