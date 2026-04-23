def load_state_dict(self, state_dict: StateDict) -> None:
        r"""Load the optimizer state.

        Args:
            state_dict (dict): optimizer state. Should be an object returned
                from a call to :meth:`state_dict`.

        .. warning::
            Make sure this method is called after initializing :class:`torch.optim.lr_scheduler.LRScheduler`,
            as calling it beforehand will overwrite the loaded learning rates.

        .. note::
            The names of the parameters (if they exist under the "param_names" key of each param group
            in :meth:`state_dict`) will not affect the loading process.
            To use the parameters' names for custom cases (such as when the parameters in the loaded state dict
            differ from those initialized in the optimizer),
            a custom ``register_load_state_dict_pre_hook`` should be implemented to adapt the loaded dict
            accordingly.
            If ``param_names`` exist in loaded state dict ``param_groups`` they will be saved and override
            the current names, if present, in the optimizer state. If they do not exist in loaded state dict,
            the optimizer ``param_names`` will remain unchanged.

        Example:
            >>> # xdoctest: +SKIP
            >>> model = torch.nn.Linear(10, 10)
            >>> optim = torch.optim.SGD(model.parameters(), lr=3e-4)
            >>> scheduler1 = torch.optim.lr_scheduler.LinearLR(
            ...     optim,
            ...     start_factor=0.1,
            ...     end_factor=1,
            ...     total_iters=20,
            ... )
            >>> scheduler2 = torch.optim.lr_scheduler.CosineAnnealingLR(
            ...     optim,
            ...     T_max=80,
            ...     eta_min=3e-5,
            ... )
            >>> lr = torch.optim.lr_scheduler.SequentialLR(
            ...     optim,
            ...     schedulers=[scheduler1, scheduler2],
            ...     milestones=[20],
            ... )
            >>> lr.load_state_dict(torch.load("./save_seq.pt"))
            >>> # now load the optimizer checkpoint after loading the LRScheduler
            >>> optim.load_state_dict(torch.load("./save_optim.pt"))

        """
        # shallow copy, to be consistent with module API
        state_dict = state_dict.copy()

        for pre_hook in self._optimizer_load_state_dict_pre_hooks.values():
            hook_result = pre_hook(self, state_dict)
            if hook_result is not None:
                state_dict = hook_result

        # Validate the state_dict
        groups = self.param_groups

        # Deepcopy as we write into saved_groups later to update state
        saved_groups = deepcopy(state_dict["param_groups"])

        if len(groups) != len(saved_groups):
            raise ValueError(
                "loaded state dict has a different number of parameter groups"
            )
        param_lens = (len(g["params"]) for g in groups)
        saved_lens = (len(g["params"]) for g in saved_groups)
        if any(
            p_len != s_len for p_len, s_len in zip(param_lens, saved_lens, strict=True)
        ):
            raise ValueError(
                "loaded state dict contains a parameter group "
                "that doesn't match the size of optimizer's group"
            )

        # Update the state
        id_map = dict(
            zip(
                chain.from_iterable(g["params"] for g in saved_groups),
                chain.from_iterable(g["params"] for g in groups),
                strict=True,
            )
        )

        def _cast(param, value, param_id=None, param_groups=None, key=None):
            r"""Make a deep copy of value, casting all tensors to device of param."""
            if isinstance(value, torch.Tensor):
                return Optimizer._process_value_according_to_param_policy(
                    param,
                    value,
                    # pyrefly: ignore [bad-argument-type]
                    param_id,
                    # pyrefly: ignore [bad-argument-type]
                    param_groups,
                    key,
                )
            elif isinstance(value, dict):
                return {
                    k: _cast(
                        param, v, param_id=param_id, param_groups=param_groups, key=k
                    )
                    for k, v in value.items()
                }
            elif isinstance(value, Iterable):
                # pyrefly: ignore [bad-instantiation]
                return type(value)(
                    # pyrefly: ignore [bad-argument-count]
                    _cast(param, v, param_id=param_id, param_groups=param_groups)
                    for v in value
                )  # type: ignore[call-arg]
            else:
                return value

        # Copy state assigned to params (and cast tensors to appropriate types).
        # State that is not assigned to params is copied as is (needed for
        # backward compatibility).
        state: defaultdict[torch.Tensor, dict[Any, Any]] = defaultdict(dict)
        for k, v in state_dict["state"].items():
            if k in id_map:
                param = id_map[k]
                state[param] = _cast(
                    param, v, param_id=k, param_groups=state_dict["param_groups"]
                )
            else:
                state[k] = v

        # Update parameter groups, setting their 'params' value
        def update_group(
            group: dict[str, Any], new_group: dict[str, Any]
        ) -> dict[str, Any]:
            new_group["params"] = group["params"]
            if "param_names" in group and "param_names" not in new_group:
                new_group["param_names"] = group["param_names"]
            return new_group

        param_groups = [
            update_group(g, ng) for g, ng in zip(groups, saved_groups, strict=True)
        ]
        self.__setstate__({"state": state, "param_groups": param_groups})

        for post_hook in self._optimizer_load_state_dict_post_hooks.values():
            post_hook(self)