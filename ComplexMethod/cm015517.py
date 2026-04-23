def _test_ignored_modules_transformer(
        self,
        use_orig_params: bool,
        ignore_modules: bool,  # as opposed to `ignored_states`
        use_auto_wrap: bool,
    ):
        # Initialize an FSDP-wrapped transformer model that has FSDP ignore
        # the `nn.Transformer` module's parameters
        model: nn.Module = TransformerWithSharedParams.init(
            self.process_group,
            FSDPInitMode.NO_FSDP,
            DEVICEInitMode.DEVICE_BEFORE,
            deterministic=True,
        )
        fsdp_kwargs = {"process_group": self.process_group}
        if use_auto_wrap:
            # Unshare the output projection weight and embedding weight to be
            # able to auto wrap every linear correctly
            model.output_proj.weight = nn.Parameter(model.output_proj.weight.clone())
            fsdp_kwargs["auto_wrap_policy"] = ModuleWrapPolicy({nn.Linear})
        if ignore_modules:
            fsdp_kwargs["ignored_modules"] = [model.transformer]
        else:
            fsdp_kwargs["ignored_states"] = list(model.transformer.parameters())
        wrapper_cls = FSDP
        wrapped_model = wrapper_cls(model, **fsdp_kwargs)
        # Check that the wrapped model's flattened parameter does not include
        # the ignored transformer module's parameters
        nonwrapped_model: nn.Module = TransformerWithSharedParams.init(
            self.process_group,
            FSDPInitMode.NO_FSDP,
            DEVICEInitMode.DEVICE_BEFORE,
            deterministic=True,
        )
        if use_auto_wrap:
            nonwrapped_model.output_proj.weight = nn.Parameter(
                nonwrapped_model.output_proj.weight.clone()
            )
        total_numel = sum(p.numel() for p in nonwrapped_model.parameters())
        ignored_numel = sum(
            p.numel() for p in nonwrapped_model.transformer.parameters()
        )
        nonignored_numel = total_numel - ignored_numel
        fsdp_managed_numel = 0
        with FSDP.summon_full_params(wrapped_model):
            for handle in traversal_utils._get_fsdp_handles(wrapped_model):
                flat_param = handle.flat_param
                flat_param_numel = flat_param.numel()
                if use_orig_params:
                    # Subtract the numel contributed from alignment padding
                    padding_numel = sum(
                        numel
                        for (numel, is_padding) in zip(
                            flat_param._numels_with_padding, flat_param._is_padding_mask
                        )
                        if is_padding
                    )
                    flat_param_numel -= padding_numel
                fsdp_managed_numel += flat_param_numel
        self.assertEqual(fsdp_managed_numel, nonignored_numel)
        # Check that we can run a few iterations
        optim = torch.optim.Adam(wrapped_model.parameters(), lr=1e-3)
        self._train_model(wrapped_model, optim, 3)