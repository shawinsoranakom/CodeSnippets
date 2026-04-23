def _validate_input(pred, true_fn, false_fn, operands):
        if not isinstance(pred, (bool, torch.Tensor, torch.SymBool)):
            raise RuntimeError(f"Expected pred to be bool or tensor, but got {pred}.")

        if isinstance(pred, torch.Tensor) and pred.numel() != 1:
            raise RuntimeError(
                f"Expected pred to be bool or single-element tensor, but got {pred}."
            )

        if not callable(true_fn) or not callable(false_fn):
            raise RuntimeError("Expect both branches to be callable.")

        if not isinstance(operands, (tuple, list)) or pytree.tree_any(
            lambda t: not isinstance(t, torch.Tensor), operands
        ):
            raise RuntimeError(
                "Expect operands to be a tuple of possibly nested dict/list/tuple that only "
                f"consists of tensor leaves, but got {operands}."
            )