def _create_model(self, compile, model_type, state_dict_options=None):
        dummy_model = TestDummyModel().to(self.device_type)

        if model_type not in ModelType:
            raise AssertionError(f"{model_type} is not supported.")
        if model_type == ModelType.FSDP:
            device_mesh = init_device_mesh(self.device_type, (self.world_size,))
            model = FSDP(
                dummy_model,
                device_mesh=device_mesh,
                use_orig_params=True,
            )
        elif model_type == ModelType.HSDP:
            device_mesh = init_device_mesh(self.device_type, (2, self.world_size // 2))
            model = FSDP(
                dummy_model,
                device_mesh=device_mesh,
                use_orig_params=True,
                sharding_strategy=ShardingStrategy.HYBRID_SHARD,
            )
        elif model_type == ModelType.FSDP_TP:
            mesh_2d = init_device_mesh(
                self.device_type, (2, self.world_size // 2), mesh_dim_names=("dp", "tp")
            )
            tp_mesh = mesh_2d["tp"]
            dp_mesh = mesh_2d["dp"]
            parallelize_plan = {
                "net1": ColwiseParallel(),
                "net2": RowwiseParallel(),
            }
            model = parallelize_module(dummy_model, tp_mesh, parallelize_plan)
            model = FSDP(model, device_mesh=dp_mesh, use_orig_params=True)
        elif model_type == ModelType.DDP:
            model = DistributedDataParallel(dummy_model)
            model.get_input = partial(TestDummyModel.get_input, model)
        else:
            model = dummy_model

        if compile:
            # TODO: enable dynamic=True when dynamic shape support is enabled.
            # model = torch.compile(model)
            model = torch.compile(model, dynamic=False)

        optim = self._optim(model)
        if model_type is not ModelType.NONE:
            _patch_model_state_dict(model, options=state_dict_options)
            _patch_optimizer_state_dict(
                model, optimizers=optim, options=state_dict_options
            )

        return model, optim