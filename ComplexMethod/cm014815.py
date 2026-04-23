def check(
        self,
        module,
        arg_or_args,
        *,
        trace_args=None,
        convert_args=None,
        atol_rtol=None,
        limit=None,
        expected_memory_format=None,
    ):
        with torch.no_grad():
            if isinstance(arg_or_args, torch.Tensor):
                args = [arg_or_args]
            else:
                args = arg_or_args
            module.eval()
            traced = torch.jit.trace(module, trace_args or args)
            nnapi_module = self.call_lowering_to_nnapi(traced, convert_args or args)
            if not self.can_run_nnapi:
                # Only test that the model was converted successfully.
                return
            eager_output = module(*args)
            nnapi_output = nnapi_module(*args)
            kwargs = {}
            if atol_rtol is not None:
                kwargs["atol"] = atol_rtol[0]
                kwargs["rtol"] = atol_rtol[1]
            self.assertEqual(eager_output, nnapi_output, **kwargs)
            if limit is not None:
                mismatches = eager_output.int_repr().to(
                    torch.int32
                ) - nnapi_output.int_repr().to(torch.int32)
                if mismatches.count_nonzero() > limit:
                    # Too many mismatches.  Re-run the check with no tolerance
                    # to get a nice message.
                    self.assertEqual(eager_output, nnapi_output, atol=0, rtol=0)
            if expected_memory_format:
                self.assertTrue(
                    nnapi_output.is_contiguous(memory_format=expected_memory_format)
                )