def test_3_level_hierarchical_model_averager(self):
            rank = dist.get_rank()
            world_size = dist.get_world_size()
            rank_to_GPU = init_multigpu_helper(world_size, BACKEND)
            device_id = rank_to_GPU[rank][0]

            model = nn.Linear(1, 5, bias=False).cuda(device_id)
            param = next(model.parameters())
            tensor = torch.ones_like(param.data) * rank
            # Set up such a hierarchical model averaging as follows:
            # after the first 10 warmup steps,
            # run model averaging every 2 steps within each subgroup of size 2,
            # run model averaging every 4 steps within each subgroup of size 3,
            # and run the global model averaging every 8 steps.
            # If there is a conflict in model averaging at a step, only run the highest-level model averaging.
            warmup_steps = 10
            subgroup_size1 = 2
            subgroup_avg_period1 = 2
            subgroup_size2 = 4
            subgroup_avg_period2 = 4
            global_avg_period = 8
            period_group_size_dict = OrderedDict(
                [
                    (subgroup_avg_period1, subgroup_size1),
                    (subgroup_avg_period2, subgroup_size2),
                    (global_avg_period, world_size),
                ]
            )
            averager = hierarchicalSGD.HierarchicalModelAverager(
                period_group_size_dict=period_group_size_dict, warmup_steps=warmup_steps
            )
            self.assertEqual(dist.get_pg_count(), len(period_group_size_dict))

            subgroup1 = averager.period_process_group_dict[subgroup_avg_period1]
            subgroup2 = averager.period_process_group_dict[subgroup_avg_period2]
            real_group_ranks_res1 = _get_pg_config(subgroup1)["ranks"]
            real_group_ranks_res2 = _get_pg_config(subgroup2)["ranks"]

            expect_group_ranks_res1 = (
                rank // subgroup_size1 * subgroup_size1
                + np.array(list(range(subgroup_size1)))
            ).tolist()
            expect_group_ranks_res2 = (
                rank // subgroup_size2 * subgroup_size2
                + np.array(list(range(subgroup_size2)))
            ).tolist()
            self.assertEqual(real_group_ranks_res1, expect_group_ranks_res1)
            self.assertEqual(real_group_ranks_res2, expect_group_ranks_res2)

            expected_avg_tensor_within_subgroup1 = (
                torch.ones_like(param.data)
                * sum(real_group_ranks_res1)
                / subgroup_size1
            )
            expected_avg_tensor_within_subgroup2 = (
                torch.ones_like(param.data)
                * sum(real_group_ranks_res2)
                / subgroup_size2
            )
            expected_global_avg_tensor = (
                torch.ones_like(param.data) * sum(range(world_size)) / world_size
            )
            for step in range(25):
                # Reset the parameters at every step.
                param.data = copy.deepcopy(tensor)
                for params in model.parameters():
                    # mock grad
                    params.grad = torch.ones_like(param.data)
                averager.average_parameters(model.parameters())
                if step == 16 or step == 24:
                    # Run global model averaging when `step` can be divided by 8.
                    self.assertEqual(param.data, expected_global_avg_tensor)
                elif step == 12 or step == 20:
                    # Run model averaging within subgroup when `step` can be divided by 4 but not by 8.
                    self.assertEqual(param.data, expected_avg_tensor_within_subgroup2)
                elif step == 10 or step == 14 or step == 18 or step == 22:
                    # Run model averaging within subgroup when `step` can be divided by 2 but not by 4 or 8.
                    self.assertEqual(param.data, expected_avg_tensor_within_subgroup1)
                else:
                    # No model averaging, so the parameters are not updated.
                    self.assertEqual(param.data, tensor)