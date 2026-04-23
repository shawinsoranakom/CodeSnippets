def test_view_as_complex(self, device, dtype):
        for xs in self.generate_simple_inputs(torch.sparse_coo, device=device, dtype=dtype):
            try:
                res = torch.view_as_complex(xs)
            except RuntimeError as e:
                if xs.shape[-1] != 2 or xs.dense_dim() == 0:
                    self.assertIn(
                        "view_as_complex_sparse is only supported for sparse tensors with the last dim == 2 and dense_dim > 0.",
                        str(e))
                elif xs._values().stride()[-1] != 1:
                    self.assertIn("Tensor must have a last dimension with stride 1", str(e))
                else:
                    raise
                continue
            self.assertEqual(res.layout, torch.sparse_coo)
            self.assertEqual(res._indices(), xs._indices())
            self.assertEqual(res.shape, xs.shape[:-1])
            self.assertEqual(res._values().real, xs._values()[..., 0])
            self.assertEqual(res._values().imag, xs._values()[..., 1])
            if not (dtype is torch.float16 and torch.device(device).type == "cpu"):
                # ComplexHalf to_dense() is not supported on CPU.
                self.assertEqual(res.to_dense(), torch.view_as_complex(xs.to_dense()))
            self.assertEqual(torch.view_as_real(torch.view_as_complex(xs)), xs)