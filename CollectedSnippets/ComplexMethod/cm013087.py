def infer_dynamic_shapes(
        self,
        set_batch_dimension_for: set[int | str] | bool | None = None,
        return_flat: bool = False,
    ) -> tuple[dict[int, Any] | None, ...] | dict[str, dict[int, Any] | None]:
        """Infers dynamic shapes based on the collected tensors.
        Most of the time, models do support a batch dimension
        but this batch dimension has the same value for every input sample.
        Instead of running inference on new samples, argument `set_batch_dimension_for`
        can be used to tell the first dimension is a dynamic dimension for a particular
        set of inputs referenced by their name (str) or their position (int).

        Args:
            set_batch_dimension_for (set[int | str] | bool | None): Set of input identifiers,
                by name (``str``) or position (``int``), for which the first dimension
                should be treated as a dynamic batch dimension. If ``None`` or empty,
                no additional batch dimensions are marked as dynamic.
            return_flat: Tells the function to return a flat tuple instead of
                nested structured. This option is used internally to infer arguments.
        """
        self.align_inputs_none_values()
        assert self._best_candidate is not None  # noqa: S101
        assert self._best_candidate.flat_list is not None  # noqa: S101
        assert self._best_candidate.aligned_flat_list is not None  # noqa: S101

        def _set_batch_dimension(name_or_position) -> bool:
            if not set_batch_dimension_for:
                return False
            if (
                isinstance(set_batch_dimension_for, bool) and set_batch_dimension_for
            ) or name_or_position in set_batch_dimension_for:
                return True
            if isinstance(name_or_position, int):
                torch._check(
                    name_or_position < len(self.signature_names),
                    lambda: f"argument at position {name_or_position} is out of boundary",
                )
                if self.signature_names[name_or_position] in set_batch_dimension_for:
                    return True
            return False

        def _set_batch_dimension_for_flat_index(index) -> bool:
            return _set_batch_dimension(
                # pyrefly: ignore[missing-attribute]
                self._best_candidate.position_to_args_kwargs[index]
            )

        if len(self._best_candidate.flat_list) != len(
            self._best_candidate.aligned_flat_list
        ):
            raise NotImplementedError(
                "infer_dynamic_shapes is not implemented "
                "when the best candidate is not 'aligned'. "
                "This happens when there is no stored set of inputs where "
                "all optional inputs showing in other sets are defined."
            )

        if len({inputs.n_aligned_tensors for inputs in self.inputs}) != 1:
            raise NotImplementedError(
                f"infer_dynamic_shapes is not implemented "
                f"when the number of input tensors are not the same in "
                f"every set of inputs "
                f"{[inputs.n_aligned_tensors for inputs in self.inputs]}."
            )
        shape_lists = [
            [(None if t is None else t.shape) for t in candidate.aligned_flat_list]
            for candidate in self.inputs
            if candidate.aligned_flat_list is not None
        ]
        n_tensors = len(shape_lists[0])
        dynamic_shapes = [
            _infer_dynamic_dimensions(
                [s for s in [shapes[index] for shapes in shape_lists] if s is not None],
                set_batch_dimension=_set_batch_dimension_for_flat_index(index),
            )
            for index in range(n_tensors)
        ]
        cst = torch.export.Dim.DYNAMIC
        flat_dynamic_shapes = [dict.fromkeys(dims, cst) for dims in dynamic_shapes]
        if return_flat:
            return tuple(flat_dynamic_shapes)

        # Let's regroup.
        if len(flat_dynamic_shapes) == len(self._best_candidate.args) + len(
            self._best_candidate.kwargs
        ):
            # It means forward method is called with tensors only.
            if (
                not self._best_candidate.kwargs
                and not self._best_candidate.cst_kwargs
                and not self.args_name_and_position
            ):
                # only positional arguments
                return tuple(flat_dynamic_shapes)
            if not self._best_candidate.args:
                # only named arguments
                ds = dict(zip(list(self._best_candidate.kwargs), flat_dynamic_shapes))
                return self._post_process_for_kwargs(
                    {**ds, **dict.fromkeys(self._best_candidate.cst_kwargs, None)}
                )
            if not self.args_name_and_position:
                # positional arguments needs to be moved to the named arguments
                n_args = len(self._best_candidate.args)
                pos_names = self.signature_names[:n_args]
                return self._post_process_for_kwargs(
                    {
                        **dict(zip(pos_names, flat_dynamic_shapes[:n_args])),
                        **dict(
                            zip(
                                list(self._best_candidate.kwargs),
                                flat_dynamic_shapes[n_args:],
                            )
                        ),
                        **dict.fromkeys(self._best_candidate.cst_kwargs, None),
                    }
                )
            # positional arguments needs to be moved to the named arguments
            n_args = min(len(self._best_candidate.args), self.args_name_and_position[1])
            i_kwargs = max(
                len(self._best_candidate.args), self.args_name_and_position[1]
            )
            var_pos = self.args_name_and_position[0]
            pos_names = self.signature_names[:n_args]
            return self._post_process_for_kwargs(
                {
                    **dict(zip(pos_names, flat_dynamic_shapes[:n_args])),
                    var_pos: tuple(flat_dynamic_shapes[n_args:i_kwargs]),
                    **dict(
                        zip(
                            list(self._best_candidate.kwargs),
                            flat_dynamic_shapes[i_kwargs:],
                        )
                    ),
                    **dict.fromkeys(self._best_candidate.cst_kwargs, None),
                }
            )

        # nested types, here comes the fun part because the shapes cannot be unflattened,
        # custom classes must appear in their flattened shape.
        # This does not work in all cases but every time every available argument is flattened
        # with the same number of tensors. The function does not check
        # if that assumption is true.
        flat_inputs, _max_spec = torch.utils._pytree.tree_flatten(
            (self._best_candidate.args, self._best_candidate.kwargs)
        )
        torch._check(
            len(flat_inputs) == len(flat_dynamic_shapes),
            (
                f"Length mismatch len(flat_inputs)={len(flat_inputs)}, "
                f"len(flat_dynamic_shapes)={len(flat_dynamic_shapes)}"
            ),
        )

        index = 0

        def change_function(t):
            nonlocal index
            if index >= len(flat_dynamic_shapes):
                raise RuntimeError(
                    f"Flattened {index} tensors when there are only "
                    f"{len(flat_dynamic_shapes)}."
                )
            res = flat_dynamic_shapes[index]
            index += 1
            return res

        ds_args, ds_kwargs = _flatten_unflatten_for_dynamic_shapes(
            (self._best_candidate.args, self._best_candidate.kwargs),
            change_function=change_function,
        )
        if self._best_candidate.cst_kwargs:
            ds_kwargs = {
                **ds_kwargs,
                **dict.fromkeys(self._best_candidate.cst_kwargs, None),
            }
        if not ds_kwargs and not self.args_name_and_position:
            return tuple(ds_args)
        if not ds_args:
            return self._post_process_for_kwargs(ds_kwargs)

        if not self.args_name_and_position:
            pos_names = self.signature_names[: len(ds_args)]
            return self._post_process_for_kwargs(
                {**dict(zip(pos_names, ds_args)), **ds_kwargs}
            )

        n_args = min(len(ds_args), self.args_name_and_position[1])
        pos_names = self.signature_names[:n_args]
        return self._post_process_for_kwargs(
            {
                **dict(zip(pos_names, ds_args[:n_args])),
                self.args_name_and_position[0]: tuple(ds_args[n_args:]),
                **ds_kwargs,
            }
        )