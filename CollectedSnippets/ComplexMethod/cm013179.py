def init(
        group: dist.ProcessGroup,
        fsdp_init_mode: FSDPInitMode,
        device_init_mode: DEVICEInitMode,
        fsdp_kwargs: dict[str, Any] | None = None,
        deterministic: bool = False,
        add_bn: bool = True,
    ) -> nn.Module | FSDP:
        """
        Initializes a :class:`TransformerWithSharedParams` instance.

        Args:
            fsdp_init_mode (FSDPInitMode): If ``NO_FSDP``, then does not wrap
                any modules with FSDP. If ``RECURSIVE``, then wraps with
                top-level FSDP. By default, the top-level FSDP uses the
                ``ModuleWrapPolicy`` for encoder and decoder layers, but a
                different auto wrap policy may be specified via
                ``fsdp_kwargs``.
            device_init_mode (DEVICEInitMode): Determines model movement to DEVICE.
            fsdp_kwargs (Optional[Dict[str, Any]]): Optional keyword arguments
                forwarded to the FSDP constructor.
            deterministic (bool): Whether to make the model deterministic
                across constructions.
            add_bn (bool): Whether to include batch norm in the model.
        """

        if fsdp_kwargs is None:
            fsdp_kwargs = {}
        if fsdp_init_mode == FSDPInitMode.NO_FSDP:
            if isinstance(group, tuple):
                pg = group[0]
            else:
                pg = group
            return TransformerWithSharedParams(
                pg, device_init_mode, add_bn, deterministic
            )
        elif fsdp_init_mode == FSDPInitMode.RECURSIVE:
            # Default to the `ModuleWrapPolicy`
            if "auto_wrap_policy" not in fsdp_kwargs:
                auto_wrap_policy = ModuleWrapPolicy(
                    {
                        TransformerEncoderLayer,
                        TransformerDecoderLayer,
                    }
                )
            else:
                auto_wrap_policy = fsdp_kwargs.pop("auto_wrap_policy")

            if (
                "sharding_strategy" in fsdp_kwargs
                and fsdp_kwargs["sharding_strategy"]
                in {ShardingStrategy.HYBRID_SHARD, ShardingStrategy._HYBRID_SHARD_ZERO2}
                and not isinstance(group, tuple)
            ):
                fsdp_pg = None
            else:
                fsdp_pg = group

            if isinstance(group, tuple):
                tformer_pg = group[0]
            else:
                tformer_pg = group

            m = TransformerWithSharedParams(
                tformer_pg, device_init_mode, add_bn, deterministic
            )
            fsdp_model = FSDP(
                m,
                fsdp_pg,
                auto_wrap_policy=auto_wrap_policy,
                **fsdp_kwargs,
            )
            if device_init_mode == DEVICEInitMode.DEVICE_AFTER:
                fsdp_model = fsdp_model.to(DEVICE_TYPE)
            return fsdp_model
        raise ValueError(f"Unsupported FSDP init mode: {fsdp_init_mode}")