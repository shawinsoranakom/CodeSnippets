def assert_nested_tensors_close(a, b):
            if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
                assert len(a) == len(b), f"Length mismatch: {len(a)} vs {len(b)}"
                for i, (x, y) in enumerate(zip(a, b)):
                    assert_nested_tensors_close(x, y)
            elif torch.is_tensor(a) and torch.is_tensor(b):
                a_clean = set_nan_tensor_to_zero(a)
                b_clean = set_nan_tensor_to_zero(b)
                assert torch.allclose(a_clean, b_clean, atol=1e-5), (
                    "Tuple and dict output are not equal. Difference:"
                    f" Max diff: {torch.max(torch.abs(a_clean - b_clean))}. "
                    f"Tuple has nan: {torch.isnan(a).any()} and inf: {torch.isinf(a)}. "
                    f"Dict has nan: {torch.isnan(b).any()} and inf: {torch.isinf(b)}."
                )
            else:
                raise ValueError(f"Mismatch between {a} vs {b}")