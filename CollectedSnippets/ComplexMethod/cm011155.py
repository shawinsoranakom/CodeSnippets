def load_state_dict(self, state_dict: dict[str, Any]) -> None:
        """
        Define the default behavior to load a state_dict for ``_NamedOptimizer``.

        Sample Code
        ```
            my_model = MyModule()
            optimizer = _NamedOptimizer(my_model.named_parameters(), Adagrad)
            ...

            optim_state_dict = optimizer.state_dict()
            ...
            ...

            optimizer.load_state_dict(optim_state_dict)
            ...
        ```
        Args:
            state_dict (dict[str, Any]) : A ``state_dict`` to load into the optimizer.
                Note that this state dict update is performed in place.

        .. note:: PyTorch is using lazy init to initialize the optim states.
            So it is possible that there is no optim state when user call
            ``load_state_dict`` and for ``_NamedOptimizer`` we make it stricter
            that users can only call ``load_state_dict`` after the state is initialized.
            By doing this, we can validate the optim ``state_dict`` to be loaded.
        """
        new_state_dict = self._optimizer.state_dict()
        state_dict = self._pre_load_state_dict(state_dict)
        state = state_dict["state"]
        new_state = new_state_dict["state"]
        if len(new_state) == 0:
            raise ValueError(
                "Expects the optim to be initialized before load but found not initialized."
            )

        for idx, param_key in enumerate(self.ordered_param_keys):
            # When the conditional training is performed, not all parameters are updated in the optim.
            if param_key not in state:
                continue
            if len(state[param_key]) != len(new_state[idx]):
                raise ValueError(
                    f"Expects equal length as {len(new_state[idx])} for parameter {param_key} but found: {len(state[param_key])}"
                )
            # Iterate through all optimizer states.
            for state_key, state_val in new_state[idx].items():
                if state_key not in state[param_key]:
                    raise ValueError(
                        f"Expects state {state_key} for parameter {param_key} but not found."
                    )

                src_state_val = state[param_key][state_key]
                if isinstance(state_val, ShardedTensor):
                    if not isinstance(src_state_val, ShardedTensor):
                        raise AssertionError
                    num_shards = len(state_val.local_shards())
                    num_new_shards = len(src_state_val.local_shards())
                    if num_shards != num_new_shards:
                        raise ValueError(
                            f"Expects equal number of shards as {num_new_shards} but found {num_shards} for {param_key}/{state_key}"
                        )
                    for shard, src_shard in zip(
                        state_val.local_shards(), src_state_val.local_shards()
                    ):
                        shard.tensor.detach().copy_(src_shard.tensor)
                elif isinstance(state_val, torch.Tensor):
                    if not isinstance(src_state_val, torch.Tensor):
                        raise AssertionError
                    state_val.detach().copy_(src_state_val)
                else:
                    new_state[idx][state_key] = deepcopy(src_state_val)

        # Load param_groups of state_dict
        src_param_groups = state_dict["param_groups"]
        new_param_groups = new_state_dict["param_groups"]

        src_group_map = {}
        for group in src_param_groups:
            param_keys = list(group["params"])
            src_group_map[_gen_param_group_key(param_keys)] = group
        new_group_map = {}
        for new_group in new_param_groups:
            param_keys = []
            for param_key in new_group["params"]:
                param_keys.append(self.ordered_param_keys[param_key])  # type: ignore[call-overload]
            new_group_map[_gen_param_group_key(param_keys)] = new_group
        for group_key, new_group in new_group_map.items():
            # When not all parameters are used in training or receive gradient, aka., not all parameters
            # would be in the param_group. Thus we skip the group_key here.
            if group_key not in src_group_map:
                continue
            src_group = src_group_map[group_key]
            if len(src_group) != len(new_group):
                raise ValueError(
                    f"Expects equal param_group size as {len(new_group)} for group {group_key} but found {len(src_group)}."
                )
            for k in src_group:
                if k not in new_group:
                    raise ValueError(
                        f"Expects group key {k} to be in group {group_key} in `state_dict` but is missing."
                    )
                if k != "params":
                    new_group[k] = deepcopy(src_group[k])

        self._optimizer.load_state_dict(new_state_dict)