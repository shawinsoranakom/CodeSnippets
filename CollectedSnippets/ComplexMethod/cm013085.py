def align_with(
        self,
        best_candidate: InputCandidate,
        captured_inputs: dict[int | str, int],
        signature_names: list[str],
    ):
        """Two candidates are considered as aligned if after being flattened
        if they have the same number of tensors (None allowed)."""
        if self.cst_kwargs != best_candidate.cst_kwargs:
            raise RuntimeError(
                f"Two calls were made with different constant values, "
                f"{self.cst_kwargs} != {best_candidate.cst_kwargs}"
            )

        args = self.args
        if len(self.args) > len(best_candidate.args):
            # We need to move some args to kwargs as the best_candidate does.
            new_kwargs = {}
            for i in range(len(best_candidate.args), len(self.args)):
                new_kwargs[signature_names[i]] = args[i]
            args = args[: len(best_candidate.args)]
            kwargs = {**new_kwargs, **self.kwargs}
        else:
            kwargs = self.kwargs

        flat = []
        for i in range(len(best_candidate.args)):
            if i < len(args) and (isinstance(args[i], torch.Tensor) or args[i]):
                ts = torch.utils._pytree.tree_flatten(self.args[i])[0]
                if i in captured_inputs and captured_inputs[i] != len(ts):
                    raise RuntimeError(
                        f"Positional argument {i} has {len(ts)} tensors "
                        f"but previously got {captured_inputs[i]} tensors. "
                        f"Inference is impossible in that case."
                    )
                captured_inputs[i] = len(ts)
                flat.extend(ts)
                continue
            # If the argument i is not specified or is None or an empty container.
            flat.extend(
                [None for _ in range(best_candidate.n_tensors_for_args_kwargs[i])]
            )

        for k in best_candidate.kwargs:
            if k in kwargs and (isinstance(kwargs[k], torch.Tensor) or kwargs[k]):
                ts = torch.utils._pytree.tree_flatten(kwargs[k])[0]
                if k in captured_inputs and captured_inputs[k] != len(ts):
                    raise RuntimeError(
                        f"Named argument {k!r} has {len(ts)} tensors "
                        f"but previously got {captured_inputs[k]} tensors in "
                        f"kwargs={list(kwargs)}. "
                        f"Inference is impossible in that case."
                    )
                captured_inputs[k] = len(ts)
                flat.extend(ts)
                continue
            # If the argument k is not specified or is None or an empty container.
            flat.extend(
                [None for _ in range(best_candidate.n_tensors_for_args_kwargs[k])]
            )

        self._set_aligned_flat_list(flat, best_candidate.spec)