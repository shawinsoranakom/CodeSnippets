def test_reduce_scatter_ops(self):
        pg = self.pg
        local_device_ids = self.rank_to_GPU[self.rank]
        num_gpus = len(local_device_ids)

        def reduce_scatter(outputs, input_lists, op):
            opts = c10d.ReduceScatterOptions()
            opts.reduceOp = op
            work = pg.reduce_scatter(outputs, input_lists, opts)
            work.wait()

        output = [torch.tensor([0]).cuda(i) for i in local_device_ids]

        #  GPU/rank
        #   0         [1], [2], [3], [4]
        #   1         [2], [3], [4], [5]
        #   2         [3], [4], [5], [6]
        #   3         [4], [5], [6], [7]

        # Sum
        tensor_lists = []
        input_per_gpu = []

        for i in range(self.world_size):
            input_per_gpu.append(torch.tensor([self.rank + i + 1]))

        for gpu in local_device_ids:
            tensor_lists.append([t.cuda(device=gpu) for t in input_per_gpu])

        reduce_scatter(output, tensor_lists, c10d.ReduceOp.SUM)

        for i in range(num_gpus):
            expected = torch.tensor(
                [
                    (1 + self.world_size) * self.world_size // 2
                    + self.world_size * self.rank
                ]
            )

            self.assertEqual(expected, output[i])

        # Min
        reduce_scatter(output, tensor_lists, c10d.ReduceOp.MIN)

        for i in range(num_gpus):
            expected = torch.tensor([self.rank + 1 + i])
            self.assertEqual(expected, output[i])

        # Max
        reduce_scatter(output, tensor_lists, c10d.ReduceOp.MAX)

        for i in range(num_gpus):
            expected = torch.tensor([self.rank + self.world_size + i])
            self.assertEqual(expected, output[i])

        # Product
        reduce_scatter(output, tensor_lists, c10d.ReduceOp.PRODUCT)

        for i in range(num_gpus):
            prod_val = math.perm(self.rank + self.world_size, self.world_size)

            expected = torch.tensor([prod_val])
            self.assertEqual(expected, output[i])

        # Test the input params overridden scenarios, aka, when the input is
        # a list and output is just one tensor.
        # Sum
        output_tensor = torch.empty_like(input_per_gpu[0][0]).cuda(self.rank)
        input_list = [tensor[0].cuda(self.rank) for tensor in input_per_gpu]
        pg.reduce_scatter(output_tensor, input_list, c10d.ReduceOp.SUM).wait()
        expected = torch.tensor(
            (1 + self.world_size) * self.world_size // 2 + self.world_size * self.rank
        )
        self.assertEqual(expected, output_tensor)

        # Min
        pg.reduce_scatter(output_tensor, input_list, c10d.ReduceOp.MIN).wait()
        expected = torch.tensor(self.rank + 1)
        self.assertEqual(expected, output_tensor)

        # Max
        pg.reduce_scatter(output_tensor, input_list, c10d.ReduceOp.MAX).wait()
        expected = torch.tensor(self.rank + self.world_size)
        self.assertEqual(expected, output_tensor)

        # Product
        pg.reduce_scatter(output_tensor, input_list, c10d.ReduceOp.PRODUCT).wait()
        prod_val = self.rank + 1
        for k in range(1, self.world_size):
            prod_val = prod_val * (self.rank + 1 + k)
        expected = torch.tensor(prod_val)
        self.assertEqual(expected, output_tensor)

        if torch.cuda.nccl.version() >= (2, 11, 1):
            for factor in (3.0, torch.tensor([5.0], device=self.rank)):
                if isinstance(factor, torch.Tensor):
                    factor_ref = factor.cpu().item()
                else:
                    factor_ref = factor
                output = [t.float() for t in output]
                tensor_lists = [[t.float() for t in tl] for tl in tensor_lists]
                output_ref = [t.float() for t in output]
                tensor_lists_ref = [
                    [t.float() * factor_ref for t in tl] for tl in tensor_lists
                ]
                reduce_scatter(output, tensor_lists, c10d._make_nccl_premul_sum(factor))
                reduce_scatter(output_ref, tensor_lists_ref, c10d.ReduceOp.SUM)
                self.assertEqual(output_ref, output)