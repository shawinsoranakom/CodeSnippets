def test_multiple_param_groups(self):
        """
        Check parity between constructing ZeRO with multiple parameter groups
        upfront versus adding parameter groups to ZeRO after construction
        versus a non-sharded optimizer.
        """
        self.create_pg(self.device)
        BATCH_SIZE, NUM_ITERS = 8, 3
        INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM = 5, 10, 5
        WD, LR = 0.01, 0.01
        model1 = torch.nn.Sequential(
            torch.nn.Linear(INPUT_DIM, HIDDEN_DIM),
            torch.nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            torch.nn.Linear(HIDDEN_DIM, OUTPUT_DIM),
        )
        model2 = copy.deepcopy(model1)
        model3 = copy.deepcopy(model1)
        model1 = model1.to(self.device)
        model2 = model2.to(self.device)
        model3 = model3.to(self.device)
        inputs = [
            torch.randn(BATCH_SIZE, INPUT_DIM).to(self.device) for _ in range(NUM_ITERS)
        ]
        # Construct `optim1` with both parameter groups upfront
        optim1 = ZeroRedundancyOptimizer(
            [
                {"params": [l.weight for l in model1], "weight_decay": 0.0},
                {"params": [l.bias for l in model1], "weight_decay": WD},
            ],
            optimizer_class=AdamW,
            lr=LR,
        )
        # Construct `optim2` by adding the second parameter after
        optim2 = ZeroRedundancyOptimizer(
            [l.weight for l in model2],
            optimizer_class=AdamW,
            lr=LR,
            weight_decay=0.0,
        )
        optim2.add_param_group({"params": [l.bias for l in model2], "weight_decay": WD})
        # Construct `optim3` as a non-sharded optimizer
        optim3 = AdamW(
            [
                {"params": [l.weight for l in model3], "weight_decay": 0.0},
                {"params": [l.bias for l in model3], "weight_decay": WD},
            ],
            lr=LR,
        )
        # Check parity over a few iterations
        for input in inputs:
            for model, optim in (
                (model1, optim1),
                (model2, optim2),
                (model3, optim3),
            ):
                optim.zero_grad()
                out = model(input)
                loss = out.sum()
                loss.backward()
                optim.step()
            for layer1, layer2, layer3 in zip(model1, model2, model3):
                torch.testing.assert_close(layer1.weight, layer2.weight)
                torch.testing.assert_close(layer1.weight, layer3.weight)
                torch.testing.assert_close(layer1.bias, layer2.bias)
                torch.testing.assert_close(layer1.bias, layer3.bias)