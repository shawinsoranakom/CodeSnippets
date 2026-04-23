def work(self, data):
        start_reduction = [False for _ in range(len(data))]
        for each_rank_data in data:
            # Can't handle reduce_scatter with multiple scatter list
            if len(each_rank_data[1]) != 1:
                raise AssertionError(
                    f"Can't handle reduce_scatter with multiple scatter list, got {len(each_rank_data[1])}"
                )
            to_scatter = each_rank_data[1][0]
            for i in range(len(to_scatter)):
                dest_tensor_on_rank_i = data[i][0]
                # Can't handle reduce_scatter with multiple output tensor
                if len(dest_tensor_on_rank_i) != 1:
                    raise AssertionError(
                        f"Can't handle reduce_scatter with multiple output tensor, got {len(dest_tensor_on_rank_i)}"
                    )
                dst_tensor_device = dest_tensor_on_rank_i[0].device
                if not start_reduction[i]:
                    # See Note [Hide collectives mutation from autograd]
                    dest_tensor_on_rank_i[0].detach().copy_(
                        to_scatter[i].to(dst_tensor_device)
                    )
                    start_reduction[i] = True
                else:
                    # See Note [Hide collectives mutation from autograd]
                    dest_tensor_on_rank_i[0].detach().add_(
                        to_scatter[i].to(dst_tensor_device)
                    )
        if self.op == dist.ReduceOp.AVG:
            num_ranks = len(data)
            for each_rank_data in data:
                # See Note [Hide collectives mutation from autograd]
                each_rank_data[0][0].detach().div_(num_ranks)