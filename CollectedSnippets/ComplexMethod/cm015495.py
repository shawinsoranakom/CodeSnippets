def _test_ddp_parity(
        self,
        device,
        max_norm: float | int,
        norm_type: float | int,
        sharding_strategy: ShardingStrategy | str,
        use_orig_params: bool,
        offload_params: bool,
    ):
        local_model = TransformerWithSharedParams.init(
            self.process_group,
            FSDPInitMode.NO_FSDP,
            DEVICEInitMode.DEVICE_BEFORE,
            deterministic=True,
        )
        ddp_model = DDP(local_model, device_ids=[device_type])
        fsdp_kwargs = {
            "cpu_offload": CPUOffload(offload_params=offload_params),
            "use_orig_params": use_orig_params,
            "device_id": device_type.type,
        }
        if sharding_strategy == "mixed_strategy":
            fsdp_model = TransformerWithSharedParams.init(
                self.process_group,
                FSDPInitMode.NO_FSDP,
                DEVICEInitMode.DEVICE_BEFORE,
                deterministic=True,
            )
            # Apply `NO_SHARD` to the encoder
            fsdp_model.transformer.encoder = FSDP(
                fsdp_model.transformer.encoder,
                sharding_strategy=ShardingStrategy.NO_SHARD,
                **fsdp_kwargs,
            )
            # Apply `FULL_SHARD` to the decoder
            fsdp_model.transformer.decoder = FSDP(
                fsdp_model.transformer.decoder,
                sharding_strategy=ShardingStrategy.FULL_SHARD,
                **fsdp_kwargs,
            )
            # TODO: FSDP's `clip_grad_norm_()` is not a static method, so we
            # must make the root module an FSDP instance
            fsdp_model = FSDP(
                fsdp_model, sharding_strategy=ShardingStrategy.FULL_SHARD, **fsdp_kwargs
            )
        else:
            fsdp_kwargs.update(
                {
                    "sharding_strategy": sharding_strategy,
                    "auto_wrap_policy": ModuleWrapPolicy(
                        {
                            TransformerEncoderLayer,
                            TransformerDecoderLayer,
                        }
                    ),
                }
            )
            fsdp_model = TransformerWithSharedParams.init(
                self.process_group,
                FSDPInitMode.RECURSIVE,
                DEVICEInitMode.DEVICE_BEFORE,
                deterministic=True,
                fsdp_kwargs=fsdp_kwargs,
            )
        LR = 1e-2
        ddp_optim = torch.optim.Adam(ddp_model.parameters(), lr=LR)
        fsdp_optim = torch.optim.Adam(fsdp_model.parameters(), lr=LR)
        device = torch.device(self.device_type)
        LARGE_FACTOR = 100
        inp = ddp_model.module.get_input(device)
        for model in (ddp_model, fsdp_model):
            out = model(*inp)
            if isinstance(model, (DDP, FSDP)):
                loss = model.module.get_loss(inp, out)
            else:
                loss = model.get_loss(inp, out)
            loss.backward()
        # Multiply gradients by a large factor to ensure that gradients will
        # actually be clipped
        for param in itertools.chain(ddp_model.parameters(), fsdp_model.parameters()):
            if (
                param.grad is not None
            ):  # gradients may be `None` for `use_orig_params=True`
                param.grad *= LARGE_FACTOR
        orig_ddp_grads = [
            param.grad.detach().clone() for param in ddp_model.parameters()
        ]
        orig_fsdp_grads = [
            param.grad.detach().clone() if param.grad is not None else None
            for param in fsdp_model.parameters()
        ]
        ddp_total_norm = torch.nn.utils.clip_grad_norm_(
            ddp_model.parameters(),
            max_norm=max_norm,
            norm_type=norm_type,
        )
        fsdp_total_norm = fsdp_model.clip_grad_norm_(
            max_norm=max_norm, norm_type=norm_type
        )
        self.assertEqual(ddp_total_norm, fsdp_total_norm)
        # Check that the gradients were modified by `clip_grad_norm_()`
        for param, orig_grad in zip(ddp_model.parameters(), orig_ddp_grads):
            if torch.equal(param.grad, orig_grad):
                raise AssertionError(
                    "Expected gradient to be modified by clip_grad_norm_()"
                )
        for param, orig_grad in zip(fsdp_model.parameters(), orig_fsdp_grads):
            if param.grad is None:
                self.assertEqual(param.grad, orig_grad)  # `None`
            else:
                if torch.equal(param.grad, orig_grad):
                    raise AssertionError(
                        "Expected gradient to be modified by clip_grad_norm_()"
                    )
        # Run an optimizer step to ensure gradients matched after clipping
        ddp_optim.step()
        fsdp_optim.step()
        with FSDP.summon_full_params(fsdp_model):
            for (n1, p1), (n2, p2) in zip(
                ddp_model.module.named_parameters(),
                fsdp_model.named_parameters(),
            ):
                self.assertEqual(n1, n2)
                self.assertEqual(p1, p2)
        if offload_params:
            # TODO: Gradient computation on CPU and GPU differ slightly causing
            # drift unrelated to `clip_grad_norm_()`.
            # https://github.com/pytorch/pytorch/issues/89133
            return
        # Run a few more iterations
        # TODO: We cannot run too many iterations, or else there is drift:
        # https://github.com/pytorch/pytorch/issues/89136
        for i in range(3):
            set_to_none = i % 2 == 0  # exercise both
            ddp_optim.zero_grad(set_to_none=set_to_none)
            fsdp_optim.zero_grad(set_to_none=set_to_none)
            inp = ddp_model.module.get_input(device)
            for model in (ddp_model, fsdp_model):
                out = model(*inp)
                out.sum().backward()
            ddp_total_norm = torch.nn.utils.clip_grad_norm_(
                ddp_model.parameters(),
                max_norm=max_norm,
                norm_type=norm_type,
            )
            fsdp_total_norm = fsdp_model.clip_grad_norm_(
                max_norm=max_norm, norm_type=norm_type
            )
            self.assertEqual(ddp_total_norm, fsdp_total_norm)
            ddp_optim.step()
            fsdp_optim.step()