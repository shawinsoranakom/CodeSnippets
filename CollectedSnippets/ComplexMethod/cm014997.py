def test_matmul_offline_tunableop(self, device, dtype):
        import os
        # Main offline tunableop test
        # NOTE: The offline tuning does not support certain tensor
        # shapes as noted below. Submatrics / matrix slices are
        # not supported at all.

        def has_any_dim_size_one(tensor: torch.Tensor):
            """Check if any dimension of a PyTorch tensor has size 1."""
            return any(dim == 1 for dim in tensor.shape)

        def is_mm_compatible(A, B):
            """Check if two matrices A and B are compatible for torch.mm."""
            return A.dim() == 2 and B.dim() == 2 and A.shape[1] == B.shape[0]

        def is_bmm_compatible(A, B):
            """Check if two 3D tensors are compatible for torch.bmm."""
            return (
                A.dim() == 3 and B.dim() == 3 and
                A.shape[0] == B.shape[0] and  # Batch size must match
                A.shape[2] == B.shape[1]  # Inner dimensions must align
            )

        with self._tunableop_ctx():
            torch.cuda.tunable.set_rotating_buffer_size(0)

            ordinal = torch.cuda.current_device()

            # record GEMM
            torch.cuda.tunable.tuning_enable(False)
            torch.cuda.tunable.record_untuned_enable(True)
            self.assertTrue(torch.cuda.tunable.record_untuned_is_enabled())

            make_arg = partial(make_tensor, device=device, dtype=dtype)
            # offline tuning only handles matmuls on two dimensional tensors
            # matmul that require broadcasting are
            # not supported either.
            # Below we check the different transA and transB combinations.
            for (size_x, size_y) in self.gen_sizes_matmul(x_dim=2, y_dim=2, matrix_size=4):
                x = make_arg(size_x, noncontiguous=False)
                y = make_arg(size_y, noncontiguous=False)

                if is_mm_compatible(x, y):
                    self.check_single_matmul(x, y)
                else:
                    continue

                if is_mm_compatible(x.t(), y):
                    self.check_single_matmul(x.t(), y)
                else:
                    continue

                if is_mm_compatible(x, y.t()):
                    self.check_single_matmul(x, y.t())
                else:
                    continue

                if is_mm_compatible(x.t(), y.t()):
                    self.check_single_matmul(x.t(), y.t())
                else:
                    continue

            # offline tuning only handles batched matmuls on
            # three dimensional tensors
            # matmul that require broadcasting are
            # not supported either.
            # Below we check the different transA and transB combinations.
            for (size_x, size_y) in self.gen_sizes_matmul(x_dim=3, y_dim=3, matrix_size=4):
                x = make_arg(size_x, noncontiguous=False)
                y = make_arg(size_y, noncontiguous=False)

                if has_any_dim_size_one(x) or has_any_dim_size_one(y):
                    continue

                if is_bmm_compatible(x, y):
                    self.check_single_matmul(x, y)
                else:
                    continue

                if is_bmm_compatible(x.transpose(1, 2), y):
                    self.check_single_matmul(x.transpose(1, 2), y)
                else:
                    continue

                if is_bmm_compatible(x, y.transpose(1, 2)):
                    self.check_single_matmul(x, y.transpose(1, 2))
                else:
                    continue

                if is_bmm_compatible(x.transpose(1, 2), y.transpose(1, 2)):
                    self.check_single_matmul(x.transpose(1, 2), y.transpose(1, 2))
                else:
                    continue

            self.assertTrue(torch.cuda.tunable.is_enabled())
            self.assertTrue(torch.cuda.tunable.tuning_is_enabled() is False)

            untuned_filename = get_tunableop_untuned_filename()

            # tuning the untuned GEMMs in file
            torch.cuda.tunable.tuning_enable(True)
            torch.cuda.tunable.record_untuned_enable(False)

            # set these to single iterations to keep it short but still exercise the code
            torch.cuda.tunable.set_max_tuning_duration(1)
            torch.cuda.tunable.set_max_tuning_iterations(1)

            ref_results = len(torch.cuda.tunable.get_results())
            torch.cuda.tunable.tune_gemm_in_file(untuned_filename)
            new_results = len(torch.cuda.tunable.get_results())

            self.assertGreater(new_results - ref_results, 0)

            results_filename = torch.cuda.tunable.get_filename()
            self.assertTrue(os.path.exists(results_filename))

            # Compare Param Signature of untuned and tuned results
            ok = self._compare_untuned_tuned_entries()
            self.assertTrue(ok)