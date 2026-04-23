def _run_autocast_outofplace(
        self,
        op,
        args,
        run_as_type,
        device,
        out_type=None,
        module=torch,
        add_kwargs=None,
        amp_dtype=torch.bfloat16,
    ):
        # helper to cast args
        def cast(val, to_type):
            if isinstance(val, torch.Tensor):
                return val.to(to_type) if val.is_floating_point() else val
            elif isinstance(val, collections.abc.Iterable):
                return type(val)(cast(v, to_type) for v in val)
            else:
                return val

        if add_kwargs is None:
            add_kwargs = {}

        self.assertFalse(torch.is_autocast_enabled(device_type=device))
        with torch.amp.autocast(device_type=device, dtype=amp_dtype):
            self.assertTrue(torch.is_autocast_enabled(device_type=device))

            out_type = out_type if out_type is not None else run_as_type
            output = output_method = None

            # Try module.* variant, if requested:
            if module is not None and hasattr(module, op):
                output = getattr(module, op)(*args, **add_kwargs)
                if isinstance(output, torch.Tensor):
                    self.assertTrue(
                        out_type == output.dtype,
                        f"autocast for torch.{op} produced {output.dtype}, should produce {out_type}",
                    )
            # Try Tensor.* variant:
            if hasattr(torch.Tensor, op):
                output_method = getattr(args[0], op)(*args[1:], **add_kwargs)
                if isinstance(output_method, torch.Tensor):
                    self.assertTrue(
                        out_type == output_method.dtype,
                        f"autocast for torch.{op} produced {output_method.dtype}, should produce torch.{out_type}",
                    )

            self.assertTrue(
                (output is not None) or (output_method is not None),
                f"{op} not found as an attribute on either Tensor or the requested module {module}",
            )

            # Accounts for ops that return Tensors, iterables, and other non-Tensors.
            # For example, lstm_cell returns a tuple and equal returns bool.
            def compare(first, second):
                if isinstance(first, torch.Tensor):
                    return torch.equal(first, second)
                elif isinstance(first, collections.abc.Iterable):
                    return all(compare(f, s) for f, s in zip(first, second, strict=False))
                else:
                    return first == second

            # If both torch.* and Tensor.* variants were found, check outputs are identical
            if (output is not None) and (output_method is not None):
                self.assertTrue(type(output) is type(output_method))
                comparison = compare(output, output_method)
                self.assertTrue(
                    comparison, f"torch.{op} result did not match Tensor.{op} result"
                )

            # Compare numerics to Python-side "autocasting" that (we expect) does the same thing
            # as the C++-side autocasting, and should be bitwise accurate.
            output_to_compare = output if output is not None else output_method
            with torch.amp.autocast(device_type=device, enabled=False):
                self.assertFalse(
                    torch.is_autocast_enabled(device_type=device)
                )

                if module is not None and hasattr(module, op):
                    control = getattr(module, op)(
                        *cast(args, run_as_type), **add_kwargs
                    )
                else:
                    control = getattr(args[0].to(run_as_type), op)(
                        *cast(args[1:], run_as_type), **add_kwargs
                    )
                self.assertTrue(type(output_to_compare) is type(control))
                comparison = compare(output_to_compare, control)
                self.assertTrue(comparison, f"torch.{op} result did not match control")
            self.assertTrue(torch.is_autocast_enabled(device_type=device))
        self.assertFalse(torch.is_autocast_enabled(device_type=device))