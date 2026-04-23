def run_test():
            tested_any = False

            for sample in samples:
                # Skip if input is not a tensor or is 0-dim
                if (
                    not isinstance(sample.input, torch.Tensor)
                    or sample.input.dim() == 0
                ):
                    continue

                # Need at least size 4 in first dimension for meaningful test
                full_size = sample.input.shape[0]
                if full_size < 4:
                    continue

                # Skip broadcast/expanded tensors (stride 0 in batch dim)
                # These don't have meaningful batch invariance since all rows are the same
                if sample.input.stride()[0] == 0:
                    continue

                # Skip samples where the op normalizes/reduces over dim 0 (batch dimension)
                # because slicing the batch changes the normalization result
                if sample_operates_on_batch_dim(op.name, sample):
                    continue

                compiled_fn = compile_fn(fn, backend)

                # Get reference output at full size
                full_args = (sample.input,) + tuple(sample.args)
                full_kwargs = sample.kwargs
                full_out = compiled_fn(*full_args, **full_kwargs)

                if not isinstance(full_out, torch.Tensor):
                    continue

                # Skip if output is 0-dim (scalar) - can't slice it
                if full_out.dim() == 0:
                    continue

                # Skip if output's first dimension doesn't match input's batch size
                # (e.g., due to broadcasting or reduction)
                if full_out.shape[0] != full_size:
                    continue

                tested_any = True

                # Test with exponentially decreasing sizes: size, size/2, size/4, ...
                size = full_size
                while size >= 1:
                    # Slice all tensor inputs with matching batch dimensions
                    sliced = slice_tensors_to_batch_size(sample, size)
                    if sliced is None:
                        break
                    sliced_input, sliced_args, sliced_kwargs = sliced

                    out = compiled_fn(sliced_input, *sliced_args, **sliced_kwargs)

                    # Verify output matches the corresponding slice of full output (bitwise)
                    self.assertEqual(out, full_out[:size], rtol=0, atol=0)

                    # Step down exponentially
                    size = size // 2

            if not tested_any:
                self.skipTest("No suitable samples found for batch invariance test")