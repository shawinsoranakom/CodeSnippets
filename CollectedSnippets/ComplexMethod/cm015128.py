def test_gradient_type_promotion(self, device):
        inputs = (
            make_tensor((4, 4), device=device, dtype=torch.float32),
            make_tensor((4, 4), device=device, dtype=torch.complex64),
            make_tensor((4, 4), device=device, dtype=torch.int64),
        )

        spacing = (
            make_tensor((1,), device='cpu', dtype=torch.float32).item(),
            make_tensor((1,), device='cpu', dtype=torch.int64).item(),
            make_tensor((1,), device='cpu', dtype=torch.complex64).item(),
            make_tensor((2,), device='cpu', dtype=torch.float32, low=0.1).tolist(),
            make_tensor((2,), device='cpu', dtype=torch.int64, low=1).tolist(),
            make_tensor((2,), device='cpu', dtype=torch.complex64).tolist(),
            [make_tensor((4,), device=device, dtype=torch.float32),
             make_tensor((4,), device=device, dtype=torch.float32)],
            [make_tensor((4,), device=device, dtype=torch.int64),
             make_tensor((4,), device=device, dtype=torch.int64)],
            [make_tensor((4,), device=device, dtype=torch.complex64),
             make_tensor((4,), device=device, dtype=torch.complex64)],
        )

        for input, spacing_or_coord, edge_order in product(inputs, spacing, [1, 2]):
            input_np = input.cpu().numpy()
            input_np = input.cpu().numpy()
            actual = torch.gradient(input, spacing=spacing_or_coord, dim=(0, 1), edge_order=edge_order)
            spacing_or_coord_wrapped = self._wrap_to_list(spacing_or_coord)
            spacing_or_coord_np = []
            if torch.is_tensor(spacing_or_coord_wrapped[0]) and torch.device(spacing_or_coord_wrapped[0].device).type != 'cpu':
                for i in range(len(spacing_or_coord_wrapped)):
                    spacing_or_coord_np.append(spacing_or_coord_wrapped[i].detach().clone().cpu().numpy())
            else:
                spacing_or_coord_np = spacing_or_coord_wrapped
            expected = np.gradient(input_np, *spacing_or_coord_np, axis=(0, 1), edge_order=edge_order)
            if actual[0].dtype == torch.complex64 and input.dtype != torch.complex64:
                for i in range(len(actual)):
                    self.assertEqual(actual[i].real, expected[i].real, exact_dtype=False)
                    # Type promotion fails on Numpy when spacing is given as complex number and input is given as real.
                    # Result is given just as real number and all the imaginary parts to be equal to zero.
                    self.assertEqual(expected[i].imag, torch.zeros(actual[i].shape), exact_dtype=False)
            else:
                actual, expected = self._inf_nan_preprocess(list(actual), list(expected))
                self.assertEqual(actual, expected, equal_nan=True, exact_dtype=False)