def infer_arguments(
        self,
        index_or_args_or_kwargs: tuple[Any] | dict[str, Any] | int | None = None,
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
            index_or_args_or_kwargs: If missing, the method selects one set of inputs
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
        self._check_captured()
        assert self.info is not None  # noqa: S101
        index_or_candidate: int | InputCandidate | None = None
        if index_or_args_or_kwargs is None or isinstance(index_or_args_or_kwargs, int):
            index_or_candidate = index_or_args_or_kwargs
        else:
            if isinstance(index_or_args_or_kwargs, tuple):
                index_or_candidate = InputCandidate(
                    args=index_or_args_or_kwargs, kwargs={}, clone=False, cst_kwargs={}
                )
            elif isinstance(index_or_args_or_kwargs, dict):
                index_or_candidate = InputCandidate(
                    args=(),
                    kwargs={
                        k: v
                        for k, v in index_or_args_or_kwargs.items()
                        if k not in self.info.default_values
                    },
                    clone=False,
                    cst_kwargs={
                        k: v
                        for k, v in index_or_args_or_kwargs.items()
                        if k in self.info.default_values
                    },
                )
            else:
                raise ValueError(
                    f"Unexpected type {type(index_or_args_or_kwargs)} "
                    f"for index_or_args_or_kwargs."
                )
            self.info.align_inputs_none_values()
            index_or_candidate.align_with(
                # pyrefly: ignore[bad-argument-type]
                self.info._best_candidate,
                # pyrefly: ignore[bad-argument-type]
                self.info._captured_inputs,
                self.info.signature_names,
            )
        return self.info.infer_arguments(
            index_or_candidate,
            flat=flat,
            as_args_kwargs=as_args_kwargs,
        )