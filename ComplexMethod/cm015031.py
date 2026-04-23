def test_meta_consistency_out_dtype_mismatch(self, device, dtype, op):
        samples = op.sample_inputs(device, dtype)

        for sample in samples:
            input, args, kwargs = (sample.input, sample.args, sample.kwargs)

            try:
                # Call the functional version of the operation, using a real device, so that
                # we get the actual expected result.
                expected = op(input, *args, **kwargs)

                if isinstance(expected, tuple):
                    # Some operations return named tuples. However, pytree does not work well
                    # with that, so we turn it into a plain tuple.
                    expected = tuple(expected)
            except Exception:
                # If that doesn't work out, go to the next sample.
                continue

            def run_on(dev):
                # Create new outputs in the desired device, with a mismatching data type of
                # the same kind.
                out = pytree.tree_map_only(
                    torch.Tensor,
                    lambda t: torch.empty_like(t, device=dev, dtype=torch.float64),
                    expected,
                )

                # Move inputs to the desired device.
                arguments = (input, args, kwargs)
                arguments = pytree.tree_map_only(
                    torch.Tensor, lambda t: t.to(dev), arguments
                )
                # Also, replace every instance of 'cpu' arguments by whatever the desired
                # device really should be.
                arguments = pytree.tree_map_only(
                    torch.device, lambda d: torch.device(dev), arguments
                )
                arguments = pytree.tree_map_only(
                    str, lambda v: dev if v == device else v, arguments
                )
                input_, args_, kwargs_ = arguments

                # Try running the operation, and return the raised error, if any.
                try:
                    op(input_, *args_, **kwargs_, out=out)
                except Exception as e:
                    return e

            # Run the operation with the sample arguments on both CPU and meta devices, capturing
            # the raised error, if any.
            device_err = run_on(device)
            meta_err = run_on("meta")

            # Check whether they disagree on the result.
            #
            # In case there is an inconsistency of whether an error was raised using the real device,
            # but not when using the meta device, we raise a RuntimeError, chaining with the captured
            # one.
            #
            # We could just assertEquals here, but chaining the errors is more informative.
            if device_err is None and meta_err is not None:
                raise RuntimeError(f"{device} didn't fail, but meta did.") from meta_err
            elif device_err is not None and meta_err is None:
                raise RuntimeError(f"{device} failed, but meta didn't.") from device_err