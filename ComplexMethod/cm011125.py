def _lazy_init(self) -> None:
        """
        Lazy initialization represents when all modules' parallelisms have
        finalized (e.g. FSDP has been applied to all desired modules). This
        means that we can determine which state is the root, and we do so by
        the 1st state to run forward.
        """
        if self._is_root is not None:
            return  # no-op: already initialized
        self._is_root = True
        if len(self._modules) > 1:
            raise RuntimeError(
                f"{self._state_name} requires a single root module but got {self._modules}"
            )
        root_module = self._modules[0]
        visited_states: set[FSDPState] = set()
        for module_name, module in root_module.named_modules():
            if (state := self._get_state_for_module(module)) is None:
                continue
            if module is not root_module:
                if state not in visited_states and state._is_root is not None:
                    raise RuntimeError(
                        f"{self._state_name} state has already been lazily initialized for "
                        f"{module_name}\n{self._state_name} requires running forward through "
                        "the root module first"
                    )
                state._is_root = False
            # A single state can map to multiple modules (e.g.
            # fully_shard([mod_a, mod_b, mod_c])), so dedup here.
            if state not in visited_states:
                self._state_ctx.all_states.append(state)
            visited_states.add(state)
        # For the root, do not reshard after forward since for training,
        # the parameters would be freed and all-gathered immediately
        if self._auto_reshard_after_forward:
            for fsdp_param_group in self._fsdp_param_groups:
                fsdp_param_group.post_forward_mesh_info = None
        self._init_fqns()
        self._init_shared_state()
        self._validate_no_duplicate_params()
        # Run parameter group lazy inits after initializing FQNs for improved
        # error messages
        for state in self._state_ctx.all_states:
            for fsdp_param_group in state._fsdp_param_groups:
                fsdp_param_group.lazy_init()