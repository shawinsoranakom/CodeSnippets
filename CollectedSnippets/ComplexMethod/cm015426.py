def assertEqual(self, lhs, rhs, **kwargs):
        mode = local_tensor_mode()
        with nullcontext() if mode is None else mode.disable():
            if isinstance(lhs, LocalTensor) and isinstance(rhs, LocalTensor):
                if not (isinstance(lhs, LocalTensor) and isinstance(rhs, LocalTensor)):
                    raise AssertionError("Expected both lhs and rhs to be LocalTensor")
                super().assertEqual(lhs._ranks, rhs._ranks)
                for r in lhs._ranks:
                    super().assertEqual(
                        lhs._local_tensors[r],
                        rhs._local_tensors[r],
                        lambda m: f"rank {r}: {m}",
                    )
            elif isinstance(lhs, LocalTensor) or isinstance(rhs, LocalTensor):
                lhs, rhs = (lhs, rhs) if isinstance(lhs, LocalTensor) else (rhs, lhs)
                for r in lhs._ranks:
                    super().assertEqual(
                        lhs._local_tensors[r], rhs, lambda m: f"rank {r}: {m}"
                    )
            else:
                return super().assertEqual(lhs, rhs, **kwargs)