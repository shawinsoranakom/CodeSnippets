def test_local_optimizer_parity(
        self,
        optimizer_class_str: str,
        maximize: bool,
    ):
        """When combined with DDP, check that a local optimizer gives the same
        results as wrapping that optimizer with ZeroRedundancyOptimizer."""
        self.create_pg(self.device)
        BATCHES = 20
        BATCH_SIZE = 64
        LR = 1e-3
        INPUT_DIM = 2
        HIDDEN_DIM = 3
        OUTPUT_DIM = 3
        torch.manual_seed(self.rank)
        np.random.seed(self.rank)
        if optimizer_class_str == "Adam":
            optimizer_class = torch.optim.Adam
        elif optimizer_class_str == "AdamW":
            optimizer_class = torch.optim.AdamW
        elif optimizer_class_str == "SGD":
            optimizer_class = torch.optim.SGD
        else:
            raise AssertionError(f"Unsupported optimizer class: {optimizer_class_str}")

        with self.context:
            # Define a base model with a different buffer for each rank
            model = torch.nn.Sequential(
                torch.nn.Linear(INPUT_DIM, HIDDEN_DIM),
                torch.nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
                torch.nn.Linear(HIDDEN_DIM, OUTPUT_DIM),
            ).to(self.device)
            model.test_buffer = torch.nn.Buffer(
                torch.ones((1), device=self.device) * self.rank,
            )
            # Define models/optimizers for DDP with ZeRO and DDP with local
            # optimizer
            defaults = {"maximize": True} if maximize else {}
            sharded_optimizer = ZeroRedundancyOptimizer(
                params=model.parameters(),
                optimizer_class=optimizer_class,
                lr=LR,
                **defaults,
            )
            sharded_ddp_model = DDP(
                module=model,
                device_ids=[self.rank] if requires_ddp_rank(self.device) else None,
                broadcast_buffers=True,
                find_unused_parameters=True,
            )
            local_model = copy.deepcopy(model).to(self.device)
            ddp_optimizer = optimizer_class(
                local_model.parameters(),
                lr=LR,
                **defaults,
            )
            ddp_model = DDP(
                local_model,
                device_ids=[self.rank] if requires_ddp_rank(self.device) else None,
                broadcast_buffers=True,
                find_unused_parameters=True,
            )
            # Check that the model is properly synchronized between ranks
            # at construction time
            self._check_same_model_params(
                sharded_ddp_model,
                ddp_model,
                "Models differ from the start",
            )

            def check_step():
                input_tensor = torch.rand((BATCH_SIZE, INPUT_DIM)).to(self.device)

                def closure_ddp(input_tensor=input_tensor):
                    ddp_optimizer.zero_grad()
                    ddp_loss = ddp_model(input_tensor).abs().sum()
                    ddp_loss.backward()
                    return ddp_loss

                def closure_sharded(input_tensor=input_tensor):
                    sharded_optimizer.zero_grad()
                    sharded_loss = sharded_ddp_model(input_tensor).abs().sum()
                    sharded_loss.backward()
                    return sharded_loss

                loss_ddp = cast(
                    torch.Tensor,
                    ddp_optimizer.step(closure=closure_ddp),
                )
                loss_sharded_optim = cast(
                    torch.Tensor,
                    sharded_optimizer.step(closure=closure_sharded),
                )
                torch.testing.assert_close(
                    loss_ddp,
                    loss_sharded_optim,
                    msg="Losses differ between local optimizer and ZeRO",
                )
                self._check_same_model_params(
                    sharded_ddp_model,
                    ddp_model,
                    "Models differ after a step",
                )

            # Check that parity is maintained
            for i in range(BATCHES):
                check_step()
                # For the second half of batches, change the parameter
                # trainability to further test parity
                if i > BATCHES // 2:
                    next(ddp_model.parameters()).requires_grad = bool(i % 2)
                    next(sharded_ddp_model.parameters()).requires_grad = bool(i % 2)

            # Check that the `state_dict` checkpoints are compatible between
            # the local optimizer and ZeRO
            REFERENCE_RANK = 0
            # - Get states
            ddp_state_dict = ddp_optimizer.state_dict()
            sharded_optimizer.consolidate_state_dict(to=REFERENCE_RANK)
            sharded_optim_state_dict = [
                sharded_optimizer.state_dict() if self.rank == REFERENCE_RANK else {}
            ]
            dist.broadcast_object_list(
                sharded_optim_state_dict,
                src=REFERENCE_RANK,
                group=dist.group.WORLD,
            )
            sharded_optim_state_dict = sharded_optim_state_dict[0]

            # - Cross-load the states
            # Run one step and check that the models are still the same
            ddp_state_dict_ref = copy.deepcopy(ddp_state_dict)
            ddp_optimizer.load_state_dict(sharded_optim_state_dict)
            sharded_optimizer.load_state_dict(ddp_state_dict)
            check_step()

            # - Reload their respective states
            # Run one step and check that the models are still the same
            ddp_optimizer.load_state_dict(ddp_state_dict_ref)
            sharded_optimizer.load_state_dict(sharded_optim_state_dict)
            check_step()