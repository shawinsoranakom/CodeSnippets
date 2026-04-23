def test_distributed_tensor_planner(self) -> None:
        CHECKPOINT_DIR = self.temp_dir

        local_tensor = torch.arange(0, 4, dtype=torch.float32)
        local_tensor_2 = torch.arange(4, 8, dtype=torch.float32)
        (model, sharded_dt, replicated_dt) = self.create_dtensor_model(
            local_tensor, local_tensor_2
        )
        state_dict = model.state_dict()

        """
        When the model is initialized, the state_dict on rank 0 are as follows when there are 4 GPUs.
        rank 0:
            OrderedDict(
                [
                    (
                        'rdt',
                        DTensor(
                            local_tensor=tensor([4., 5., 6., 7.], device=f'{self.device_type}:0'),
                            device_mesh=DeviceMesh:([0, 1, 2, 3]),
                            placements=[Replicate()]
                        )
                    ),
                    (
                        'sdt',
                        DTensor(
                            local_tensor=tensor([0.], device=f'{self.device_type}:0'),
                            device_mesh=DeviceMesh:([0, 1, 2, 3]),
                            placements=[Shard(dim=0)])
                        ),
                    ),
                    (
                        'submesh_sdt',
                        DTensor(
                            local_tensor=tensor([8., 9.], device=f'{self.device_type}:0'),
                            device_mesh=DeviceMesh:([0, 2]),
                            placements=[Shard(dim=0)]
                        ),
                    ),
                    (
                        'submesh_rdt',
                        DTensor(
                            local_tensor=tensor([12., 13., 14., 15.], device=f'{self.device_type}:0'),
                            device_mesh=DeviceMesh:([0, 2]),
                            placements=[Replicate()]
                        )
                    ),
                    (
                        '_extra_state',
                        {'extra_state': 1, 'extra_state_tensor': tensor([0.])}
                    )
                ]
            )
        """

        dist_cp.save(
            state_dict=state_dict,
            storage_writer=dist_cp.FileSystemWriter(path=CHECKPOINT_DIR),
            planner=dist_cp.DefaultSavePlanner(),
        )
        model, _, _ = self.create_dtensor_model(local_tensor * 10, local_tensor_2 * 10)
        state_dict = model.state_dict()

        """
        When the model is re-initialized, we have changed the params in state_dict.
        The updated values are as follows, when there are 4 GPUs:
        rank 0:
            OrderedDict(
                [
                    (
                        'rdt',
                        DTensor(
                            local_tensor=tensor([40., 50., 60., 70.], device=f'{self.device_type}:0'),
                            device_mesh=DeviceMesh:([0, 1, 2, 3]),
                            placements=[Replicate()],
                        )
                    ),
                    (
                        'sdt',
                        DTensor(
                            local_tensor=tensor([0.], device=f'{self.device_type}:0'),
                            device_mesh=DeviceMesh:([0, 1, 2, 3]),
                            placements=[Shard(dim=0)],
                        )
                    ),
                    (
                        'submesh_sdt',
                        DTensor(
                            local_tensor=tensor([80., 90.], device=f'{self.device_type}:0'),
                            device_mesh=DeviceMesh:([0, 2]),
                            placements=[Shard(dim=0)]
                        )
                    ),
                    ('submesh_rdt',
                        DTensor(
                            local_tensor=tensor([120., 130., 140., 150.], device=f'{self.device_type}:0'),
                            device_mesh=DeviceMesh:([0, 2]),
                            placements=[Replicate()]
                        )
                    ),
                    (
                        '_extra_state', {'extra_state': 10, 'extra_state_tensor': tensor([10.])}
                    )
                ]
            )
        """

        dist_cp.load(
            state_dict=state_dict,
            storage_reader=dist_cp.FileSystemReader(CHECKPOINT_DIR),
            planner=dist_cp.DefaultLoadPlanner(),
        )

        """
        After loading the model from the checkpoint, we want to make sure that the values in state_dict
        match the values that are originally saved to the checkpoint.
        """
        for k, v in state_dict.items():
            if k == "sdt":
                self.assertEqual(sharded_dt.to_local(), v.to_local())
            if k == "rdt":
                self.assertEqual(replicated_dt.to_local(), v.to_local())

            if k == "submesh_sdt":
                if self.rank % 2 == 0:
                    shard_size = int(SUBMESH_TENSOR_SIZE / v.device_mesh.size())
                    self.assertEqual(v.to_local().size(), torch.Size([shard_size]))
                    self.assertEqual(v.to_local(), torch.zeros([shard_size]))
                else:
                    self.assertEqual(v.to_local().size(), torch.Size([0]))
                    self.assertEqual(v.to_local(), torch.tensor([]))

            if k == "submesh_rdt":
                if self.rank % 2 == 0:
                    shard_size = SUBMESH_TENSOR_SIZE
                    self.assertEqual(v.to_local().size(), torch.Size([shard_size]))
                    self.assertEqual(v.to_local(), torch.zeros([shard_size]))
                else:
                    self.assertEqual(v.to_local().size(), torch.Size([0]))
                    self.assertEqual(v.to_local(), torch.tensor([]))

            if k == "_extra_state":
                self.assertEqual(1, v["extra_state"])
                self.assertEqual(torch.tensor([0.0]), v["extra_state_tensor"])