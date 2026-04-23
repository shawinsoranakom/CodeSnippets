def infer_arguments(
        self,
        index_or_candidate: InputCandidate | int | None = None,
        /,
        flat: bool = False,
        as_args_kwargs: bool = False,
    ) -> (
        list[torch.Tensor | None]
        | tuple[torch.Tensor, ...]
        | dict[str, torch.Tensor]
        | tuple[list[torch.Tensor] | tuple[torch.Tensor, ...], dict[str, torch.Tensor]]
    ):
        """Infers arguments based on the collected tensors.

        Args:
            index_or_candidate: If missing, the method selects one set of inputs
                among the available ones, usually the set of inputs containing
                with the highest number of tensors.
                It then replaces None values and missing tensors with empty tensors.
                If not missing, it can be an integer to fetch one of the stored set
                or some inputs.
            flat: If True, it returns a flattened list of tensors,
                if False, it returns a tuple or a dictionary preserving
                the nested structures. The flat version is used internally.
                It produces a single list of tensors easier to process or modify
                rather than a nested structure holding the same tensors.
                The original structure can be restored with
                ``torch.utils._pytree.tree_unflatten(flat_list, self.aligned_spec)``.
                This mechanism is used to replace None values by empty tensors.
            as_args_kwargs: If True, the method always returns `(args, kwargs)`,
                otherwise, it returns either a tuple (only args) or a dictionary
                (only kwargs) or raises an exception if it cannot do so.
        Returns:
            Inferred arguments, every optional tensor is replaced by an empty tensor.
        """
        # This is already checked by _build_inputs_completed_with_none_values
        # but this is not always well captured by tools checking types.
        self.align_inputs_none_values()
        assert self._best_candidate is not None  # noqa: S101
        candidate = None
        if index_or_candidate is None:
            for cand in self.inputs:
                args, kwargs = cand.args, cand.kwargs
                if len(args) == len(self._best_candidate.args or ()) and len(
                    kwargs
                ) == len(self._best_candidate.kwargs or {}):
                    candidate = cand
                    break
        elif isinstance(index_or_candidate, int):
            torch._check(
                index_or_candidate < len(self.inputs),
                lambda: (
                    f"No stored input set for index="
                    f"{index_or_candidate}<{len(self.inputs)}."
                ),
            )
            candidate = self.inputs[index_or_candidate]
        else:
            candidate = index_or_candidate

        assert candidate is not None  # noqa: S101
        if candidate.aligned_flat_list is None:
            raise RuntimeError(
                f"Candidate {candidate} has no aligned flat list of tensors, "
                f"index_or_candidate={index_or_candidate}. You should call "
                f"method 'align_with'."
            )

        aligned_flat_list = candidate.aligned_flat_list
        assert aligned_flat_list is not None  # noqa: S101
        if any(t is None for t in aligned_flat_list):
            dynamic_shapes = self.infer_dynamic_shapes(return_flat=True)
            assert isinstance(dynamic_shapes, tuple)  # noqa: S101
            aligned_flat_list = list(aligned_flat_list)
            for index in range(len(aligned_flat_list)):
                if aligned_flat_list[index] is not None:
                    continue
                shape = dynamic_shapes[index]
                all_non_empty_tensors = [
                    c.aligned_flat_list[index]
                    for c in self.inputs
                    if c.aligned_flat_list is not None
                ]
                all_non_empty_tensors_not_none = [
                    t for t in all_non_empty_tensors if t is not None
                ]
                if not all_non_empty_tensors_not_none:
                    raise RuntimeError(
                        f"There is no tensor at position {index} in any flattened inputs."
                    )
                tensor = all_non_empty_tensors_not_none.pop()
                if tensor.numel() == 0:
                    aligned_flat_list[index] = tensor
                    continue
                if not shape:
                    aligned_flat_list[index] = torch.zeros(
                        tensor.shape, dtype=tensor.dtype, device=tensor.device
                    )
                    continue
                dim = max(shape)
                torch._check(
                    dim < tensor.ndim,
                    lambda index=index, shape=shape, tshape=tensor.shape: (
                        f"Tensor shape {tshape} does not match the "
                        f"dynamic shape {shape} at position {index}."
                    ),
                )
                new_shape = list(tensor.shape)
                new_shape[dim] = 0
                aligned_flat_list[index] = torch.empty(
                    tuple(new_shape), dtype=tensor.dtype, device=tensor.device
                )
        if flat:
            return aligned_flat_list
        args, kwargs = torch.utils._pytree.tree_unflatten(
            aligned_flat_list,
            # pyrefly: ignore[bad-argument-type]
            candidate.aligned_spec,
        )
        if self._best_candidate.cst_kwargs:
            kwargs = {**kwargs, **self._best_candidate.cst_kwargs}

        if not as_args_kwargs:
            if not kwargs:
                return args
            if not args:
                return kwargs

            # We need to move args to kwargs
            if self.args_name_and_position:
                raise RuntimeError(
                    "Cannot return arguments "
                    "as a single tuple or a single dictionary "
                    "because of '*args' in the function signature. "
                    "You need to set `as_args_kwargs=True`."
                )
            n_args = len(args)
            pos_names = self.signature_names[:n_args]
            return {**dict(zip(pos_names, args[:n_args])), **kwargs}

        # Generic case.
        return tuple(args), kwargs