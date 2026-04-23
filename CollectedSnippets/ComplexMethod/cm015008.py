def run_test_case(input, ord, dim, keepdim, norm_dtype):
            if isinstance(ord, complex):
                error_msg = "Expected a non-complex scalar"
                with self.assertRaisesRegex(RuntimeError, error_msg):
                    torch.linalg.vector_norm(input, ord, dim=dim, keepdim=keepdim, dtype=norm_dtype)
            elif (input.numel() == 0 and
                  (ord < 0. or ord == inf) and
                  (dim is None or input.shape[dim] == 0)):
                # The operation does not have an identity.
                error_msg = "linalg.vector_norm cannot compute"
                with self.assertRaisesRegex(RuntimeError, error_msg):
                    torch.linalg.vector_norm(input, ord, dim=dim, keepdim=keepdim)
            else:
                msg = (f'input.size()={input.size()}, ord={ord}, dim={dim}, '
                       f'keepdim={keepdim}, dtype={dtype}, norm_dtype={norm_dtype}')
                result_dtype_reference = vector_norm_reference(input, ord, dim=dim, keepdim=keepdim, dtype=norm_dtype)
                result_dtype = torch.linalg.vector_norm(input, ord, dim=dim, keepdim=keepdim, dtype=norm_dtype)
                if dtype.is_complex:
                    result_dtype_reference = result_dtype_reference.real
                self.assertEqual(result_dtype, result_dtype_reference, msg=msg)

                if norm_dtype is not None:
                    ref = torch.linalg.vector_norm(input.to(norm_dtype), ord, dim=dim, keepdim=keepdim)
                    actual = torch.linalg.vector_norm(input, ord, dim=dim, keepdim=keepdim, dtype=norm_dtype)
                    self.assertEqual(ref, actual, msg=msg)