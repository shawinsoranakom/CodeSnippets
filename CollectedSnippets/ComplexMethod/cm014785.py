def test_autocast_torch_bf16(self):
        with torch.backends.cudnn.flags(enabled=True, deterministic=True):
            for op_with_args in self.autocast_lists.torch_fp16:
                skip_test = False
                op, args = op_with_args[0], op_with_args[1]
                if len(op_with_args) == 3:
                    skip_test = op_with_args[2]  # TEST_WITH_ROCM
                should_error_from_cudnn = "cudnn" in op and (
                    "TORCH_CUDNN_V8_API_DISABLED" in os.environ
                    and int(os.environ["TORCH_CUDNN_V8_API_DISABLED"])
                    or torch.cuda.get_device_capability() < (8, 0)
                )
                should_error_from_not_implemented = should_error_from_cudnn
                if not skip_test:
                    if should_error_from_not_implemented:
                        with self.assertRaises(
                            RuntimeError,
                            msg=str(op) + " should not be supported for bfloat16!",
                        ):
                            self._run_autocast_outofplace(
                                op, args, torch.bfloat16, device="cuda"
                            )
                    else:
                        if torch.cuda.is_bf16_supported():
                            self._run_autocast_outofplace(
                                op, args, torch.bfloat16, device="cuda"
                            )
                        else:
                            with self.assertRaisesRegex(
                                RuntimeError, "Device does not support bfloat16"
                            ):
                                self._run_autocast_outofplace(
                                    op, args, torch.bfloat16, device="cuda"
                                )