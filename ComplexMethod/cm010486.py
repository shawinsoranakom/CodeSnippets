def assert_helper(a: Any, b: Any) -> None:
            if isinstance(a, tuple):
                if not isinstance(b, tuple):
                    raise AssertionError(f"Expected tuple, got {type(b)}")
                if len(a) != len(b):
                    raise AssertionError(f"Tuple length mismatch: {len(a)} != {len(b)}")
                for l, r in zip(a, b):
                    assert_helper(l, r)
            elif isinstance(a, int):
                if not isinstance(b, int) or a != b:
                    raise AssertionError(f"Int mismatch: {a} != {b}")
            elif a is None:
                if b is not None:
                    raise AssertionError(f"Expected None, got {b}")
            elif isinstance(a, py_sym_types):
                if type(a) is not type(b) or a.node is not b.node:
                    raise AssertionError(f"SymType mismatch: {a} != {b}")
            elif isinstance(a, torch.Tensor):
                if not isinstance(b, torch.Tensor):
                    raise AssertionError(f"Expected Tensor, got {type(b)}")
                assert_metadata_eq(assert_eq, a, b)
            else:
                raise RuntimeError(f"Unsupported type {type(a)}")