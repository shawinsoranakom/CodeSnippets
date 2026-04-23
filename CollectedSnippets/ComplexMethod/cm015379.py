def test_save_load_checkpoint(self):
        dist.init_process_group(
            "gloo",
            init_method=f"file://{self.file_name}",
            world_size=self.world_size,
            rank=self.rank,
        )

        class TestModel(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.fc1 = nn.Linear(2, 10, bias=False)
                self.fc2 = nn.Linear(10, 4, bias=False)
                self.relu = nn.ReLU()

            def forward(self, x):
                x = self.relu(self.fc1(x))
                x = self.relu(self.fc2(x))
                return F.softmax(x, dim=1)

        def train_loop(model, optimizer, iterations):
            for _ in range(iterations):
                optimizer.zero_grad()
                output = model(input)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()

        device_id = gpus_for_rank(self.world_size)[self.rank][0]

        model_withload = TestModel().float().to(device_id)
        model_withoutload = TestModel().float().to(device_id)

        ddp_withload = DistributedDataParallel(
            model_withload,
            device_ids=[device_id],
        )
        ddp_withoutload = DistributedDataParallel(
            model_withoutload,
            device_ids=[device_id],
        )

        # ensure that all the three models start with the same set of parameters. By default they are randomized on construction
        for p in ddp_withload.parameters():
            with torch.no_grad():
                p.zero_()
        for p in model_withload.parameters():
            with torch.no_grad():
                p.zero_()
        for p in ddp_withoutload.parameters():
            with torch.no_grad():
                p.zero_()

        batch_size = 4
        criterion = nn.CrossEntropyLoss()

        optimizer_withload = torch.optim.SGD(ddp_withload.parameters(), lr=0.001)
        optimizer_non_ddp_withload = torch.optim.SGD(
            model_withload.parameters(), lr=0.001
        )
        optimizer_withoutload = torch.optim.SGD(ddp_withoutload.parameters(), lr=0.001)

        input = torch.rand([batch_size, 2], dtype=torch.float).to(device_id)
        target = torch.LongTensor([random.randrange(4) for _ in range(batch_size)]).to(
            device_id
        )

        # run the model for 6 iterations, with a checkpoint in the middle
        train_loop(ddp_withload, optimizer_withload, 3)

        # zero out parameters of both DDP and non-DDP models and reload them from the DDP state dict
        checkpoint_path = tempfile.gettempdir() + "/model.checkpoint"
        if self.rank == 0:
            torch.save(ddp_withload.state_dict(), checkpoint_path)

        dist.barrier()
        map_location = {"cuda:0": f"cuda:{self.rank:d}"}
        ddp_state_dict = torch.load(checkpoint_path, map_location=map_location)

        for model in [ddp_withload, model_withload]:
            for p in model.parameters():
                with torch.no_grad():
                    p.zero_()
        ddp_withload.load_state_dict(ddp_state_dict)
        # the non-DDP model needs to first remove the prefix of "module." from the DDP state dict
        torch.nn.modules.utils.consume_prefix_in_state_dict_if_present(
            ddp_state_dict, "module."
        )
        model_withload.load_state_dict(ddp_state_dict)

        train_loop(ddp_withload, optimizer_withload, 3)
        train_loop(model_withload, optimizer_non_ddp_withload, 3)

        # re-run the model with the same inputs for 6 iterations with no checkpoint
        train_loop(ddp_withoutload, optimizer_withoutload, 6)

        for p_withload, p_withoutload, p_non_ddp_withload in zip(
            ddp_withload.parameters(),
            ddp_withoutload.parameters(),
            model_withload.parameters(),
        ):
            self.assertEqual(p_withload, p_withoutload)
            self.assertEqual(p_non_ddp_withload, p_withoutload)