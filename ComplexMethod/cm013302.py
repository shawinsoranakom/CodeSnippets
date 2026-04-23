def _test_ddp_buffer_hook_allreduce(self, return_futures):
            rank = self.rank
            torch.cuda.set_device(rank)
            torch.manual_seed(rank)
            torch.cuda.manual_seed(rank)

            def buffer_comm_hook(ddp, named_buffers):
                buffers = [buffer for (_, buffer) in named_buffers.items()]
                futs = [
                    dist.all_reduce(
                        buffer, group=ddp.process_group, async_op=True
                    ).get_future()
                    for buffer in buffers
                ]
                if return_futures:
                    return futs
                else:
                    torch.futures.collect_all(futs).wait()

            hook_pre_fwd = (
                torch.nn.parallel.distributed._BufferCommHookLocation.PRE_FORWARD
            )
            hook_post_fwd = (
                torch.nn.parallel.distributed._BufferCommHookLocation.POST_FORWARD
            )
            for hook_run_location in [
                hook_pre_fwd,
                hook_post_fwd,
            ]:
                model = NetWithBuffers().cuda(rank)
                model_ddp = torch.nn.parallel.DistributedDataParallel(
                    model,
                    device_ids=[self.rank],
                )
                model_ddp._register_buffer_comm_hook(
                    model_ddp, buffer_comm_hook, hook_run_location
                )
                model_ddp_no_hook = torch.nn.parallel.DistributedDataParallel(
                    copy.deepcopy(model),
                    device_ids=[self.rank],
                    broadcast_buffers=False,
                )
                inp = torch.randn(2, 10, device=rank)
                for _ in range(2):
                    loss_hook = model_ddp(inp).sum()
                    # Since buffer reduction is done pre-forward, simulate it for
                    # no hook case here.
                    # Simulate allreduce appropriately depending on hook location.
                    if hook_run_location == hook_pre_fwd:
                        model_no_hook_buffers = list(model_ddp_no_hook.module.buffers())
                        for tensor in model_no_hook_buffers:
                            dist.all_reduce(tensor)

                    loss_no_hook = model_ddp_no_hook(inp).sum()
                    if hook_run_location == hook_post_fwd:
                        model_no_hook_buffers = list(model_ddp_no_hook.module.buffers())
                        for tensor in model_no_hook_buffers:
                            dist.all_reduce(tensor)
                    torch.cuda.synchronize()

                    # if return_futures, they are only awaited on by DDP
                    # at the end of the backwards pass for maximum overlap.
                    if not return_futures:
                        self._verify_buffers_equal(model_ddp, model_ddp_no_hook)
                    loss_hook.backward()
                    loss_no_hook.backward()
                    # Note that when custom hooks return futures, this
                    # comparison is not expected to work when hook run location
                    # is pre-forward pass. This is because the hook does async
                    # communication and forward pass modifies the buffer without
                    # appropriate synchronization. Therefore, if returning
                    # futures from custom buffer hooks, it is advised to set
                    # hook run location to post forward.
                    if return_futures and hook_run_location == hook_post_fwd:
                        self._verify_buffers_equal(model_ddp, model_ddp_no_hook)
                dist.barrier()