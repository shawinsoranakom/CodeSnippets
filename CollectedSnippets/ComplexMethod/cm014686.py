def test_numpy_scalar_cmp(self, device, dtype):
        if dtype.is_complex:
            tensors = (
                torch.tensor(complex(1, 3), dtype=dtype, device=device),
                torch.tensor([complex(1, 3), 0, 2j], dtype=dtype, device=device),
                torch.tensor(
                    [[complex(3, 1), 0], [-1j, 5]], dtype=dtype, device=device
                ),
            )
        else:
            tensors = (
                torch.tensor(3, dtype=dtype, device=device),
                torch.tensor([1, 0, -3], dtype=dtype, device=device),
                torch.tensor([[3, 0, -1], [3, 5, 4]], dtype=dtype, device=device),
            )

        for tensor in tensors:
            if dtype == torch.bfloat16:
                with self.assertRaises(TypeError):
                    np_array = tensor.cpu().numpy()
                continue

            np_array = tensor.cpu().numpy()
            for t, a in product(
                (tensor.flatten()[0], tensor.flatten()[0].item()),
                (np_array.flatten()[0], np_array.flatten()[0].item()),
            ):
                self.assertEqual(t, a)
                if (
                    dtype == torch.complex64
                    and torch.is_tensor(t)
                    and type(a) is np.complex64
                ):
                    # TODO: Imaginary part is dropped in this case. Need fix.
                    # https://github.com/pytorch/pytorch/issues/43579
                    self.assertFalse(t == a)
                else:
                    self.assertTrue(t == a)