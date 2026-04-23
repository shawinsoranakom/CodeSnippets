def set_state_dict_type(
        module: nn.Module,
        state_dict_type: StateDictType,
        state_dict_config: StateDictConfig | None = None,
        optim_state_dict_config: OptimStateDictConfig | None = None,
    ) -> StateDictSettings:
        """Set the ``state_dict_type`` of all the descendant FSDP modules of the target module.

        Also takes (optional) configuration for the model's and optimizer's state dict.
        The target module does not have to be a FSDP module. If the target
        module is a FSDP module, its ``state_dict_type`` will also be changed.

        .. note:: This API should be called for only the top-level (root)
            module.

        .. note:: This API enables users to transparently use the conventional
            ``state_dict`` API to take model checkpoints in cases where the
            root FSDP module is wrapped by another ``nn.Module``. For example,
            the following will ensure ``state_dict`` is called on all non-FSDP
            instances, while dispatching into `sharded_state_dict` implementation
            for FSDP:

        Example::

            >>> # xdoctest: +SKIP("undefined variables")
            >>> model = DDP(FSDP(...))
            >>> FSDP.set_state_dict_type(
            >>>     model,
            >>>     StateDictType.SHARDED_STATE_DICT,
            >>>     state_dict_config = ShardedStateDictConfig(offload_to_cpu=True),
            >>>     optim_state_dict_config = OptimStateDictConfig(offload_to_cpu=True),
            >>> )
            >>> param_state_dict = model.state_dict()
            >>> optim_state_dict = FSDP.optim_state_dict(model, optim)

        Args:
            module (torch.nn.Module): Root module.
            state_dict_type (StateDictType): the desired ``state_dict_type`` to set.
            state_dict_config (Optional[StateDictConfig]): the configuration for the
                target ``state_dict_type``.
            optim_state_dict_config (Optional[OptimStateDictConfig]): the configuration
                for the optimizer state dict.

        Returns:
            A StateDictSettings that include the previous state_dict type and
            configuration for the module.
        """
        warnings.warn(
            "FSDP.state_dict_type() and FSDP.set_state_dict_type() are being "
            "deprecated. Please use APIs, get_state_dict() and set_state_dict(), "
            "which can support different parallelisms, FSDP1, FSDP2, DDP. "
            "API doc: https://pytorch.org/docs/stable/distributed.checkpoint.html"
            "#torch.distributed.checkpoint.state_dict.get_state_dict ."
            "Tutorial: https://pytorch.org/tutorials/recipes/distributed_checkpoint_recipe.html .",
            FutureWarning,
            stacklevel=2,
        )
        _state_dict_type_to_config = {
            StateDictType.FULL_STATE_DICT: FullStateDictConfig,
            StateDictType.LOCAL_STATE_DICT: LocalStateDictConfig,
            StateDictType.SHARDED_STATE_DICT: ShardedStateDictConfig,
        }
        _optim_state_dict_type_to_config = {
            StateDictType.FULL_STATE_DICT: FullOptimStateDictConfig,
            StateDictType.LOCAL_STATE_DICT: LocalOptimStateDictConfig,
            StateDictType.SHARDED_STATE_DICT: ShardedOptimStateDictConfig,
        }

        # Use the default config if a state_dict config is not set.
        state_dict_config_type = _state_dict_type_to_config[state_dict_type]
        optim_state_dict_config_type = _optim_state_dict_type_to_config[state_dict_type]
        if state_dict_config is None:
            state_dict_config = state_dict_config_type()
        if optim_state_dict_config is None:
            optim_state_dict_config = optim_state_dict_config_type()
        if state_dict_config_type is not type(state_dict_config):
            raise RuntimeError(
                f"Expected state_dict_config of type {state_dict_config_type} "
                f"but got {type(state_dict_config)}"
            )
        if optim_state_dict_config_type is not type(optim_state_dict_config):
            raise RuntimeError(
                f"Expected optim_state_dict_config of type {optim_state_dict_config_type} "
                f"but got {type(optim_state_dict_config)}"
            )

        # Set the state_dict type and configurations.
        prev_state_dict_type = None
        prev_state_dict_config = None
        prev_optim_state_dict_config = None
        for submodule in traversal_utils._get_fsdp_states(module):
            if prev_state_dict_type is None:
                prev_state_dict_type = submodule._state_dict_type
            else:
                if prev_state_dict_type != submodule._state_dict_type:
                    raise AssertionError(
                        "All FSDP modules should have the same state_dict_type."
                    )
            if prev_state_dict_config is None:
                prev_state_dict_config = submodule._state_dict_config
            else:
                if not isinstance(
                    submodule._state_dict_config, type(prev_state_dict_config)
                ):
                    raise AssertionError(
                        "All FSDP modules must have the same type of state_dict_config."
                    )
            if prev_optim_state_dict_config is None:
                prev_optim_state_dict_config = submodule._optim_state_dict_config
            else:
                if not isinstance(
                    submodule._optim_state_dict_config,
                    type(prev_optim_state_dict_config),
                ):
                    raise AssertionError(
                        "All FSDP modules must have the same type of optim_state_dict_config."
                    )

            submodule._state_dict_type = state_dict_type
            submodule._state_dict_config = state_dict_config
            submodule._optim_state_dict_config = optim_state_dict_config

        return StateDictSettings(
            prev_state_dict_type, prev_state_dict_config, prev_optim_state_dict_config
        )