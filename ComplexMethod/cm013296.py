def _test_ddp_ignore_params_arg(self, static_graph=False):
            class TestModel(nn.Module):
                def __init__(self, rank):
                    self.rank = rank
                    super().__init__()
                    self.fc1 = nn.Linear(1, 1, bias=False)
                    # Proxy that will be materialized to another architecture later.
                    # (after wrapping model with DDP)
                    if self.rank == 0:
                        self.fc2 = nn.Linear(1, 10, bias=False)
                    else:
                        self.fc2 = nn.Linear(10, 10, bias=False)

                def forward(self, x):
                    x = self.fc1(x)
                    x = self.fc2(x)
                    return x

            device_id = self.rank
            # Ensure the test works for both find_unused_parameter and broadcast_buffer settings.
            for find_unused, broadcast_buffers in itertools.product(
                [False, True], [False, True]
            ):
                model = TestModel(self.rank).float().to(device_id)
                # Note that the model can have different shape buffers if we pass
                # them in to be ignored as well.
                model.fc2.register_buffer(
                    "ignore_buffer", torch.zeros(5 + self.rank, device=self.rank)
                )
                proxy_params = list(model.fc2.parameters())
                model_fc2_name = next(
                    module_name
                    for module_name, module in model.named_modules()
                    if module is model.fc2
                )
                proxy_param_names = [
                    f"{model_fc2_name}.{param_name}"
                    for param_name, _ in model.fc2.named_parameters()
                ]
                proxy_buffer_names = [
                    f"{model_fc2_name}.{buf_name}"
                    for buf_name, _ in model.fc2.named_buffers()
                ]
                # Specify that we should ignore proxy_params since it will be
                # materialized later.
                torch.nn.parallel.DistributedDataParallel._set_params_and_buffers_to_ignore_for_model(
                    model, proxy_param_names + proxy_buffer_names
                )
                ddp = torch.nn.parallel.DistributedDataParallel(
                    model,
                    device_ids=[device_id],
                    find_unused_parameters=find_unused,
                    broadcast_buffers=broadcast_buffers,
                    static_graph=static_graph,
                )
                # Materialize new params. These are not registered in DDP and thus
                # don't have autograd hooks installed on them.
                ddp.module.fc2 = nn.Linear(1, 1, bias=False).to(device_id)

                # local model with the new materialized parameters.
                local_model = copy.deepcopy(ddp.module).cuda(self.rank)

                inp = torch.ones(1, dtype=torch.float).to(device_id) * (self.rank + 1)
                for _ in range(6):
                    ddp(inp).sum().backward()

                    local_model(inp).sum().backward()
                    # materialized param grad is not touched by DDP, so its grad should
                    # be the same as if running locally.
                    for materialized_param, local_param in zip(
                        ddp.module.fc2.parameters(),
                        local_model.fc2.parameters(),
                        strict=True,
                    ):
                        self.assertEqual(materialized_param.grad, local_param.grad)

                    # fc1 parameter grad should still be different, due to allreduce.
                    for synced_param, local_param in zip(
                        ddp.module.fc1.parameters(),
                        local_model.fc1.parameters(),
                        strict=True,
                    ):
                        self.assertFalse(synced_param.grad == local_param.grad)

                    # Proxy module grad should not be touched
                    for proxy_param in proxy_params:
                        self.assertTrue(proxy_param.grad is None)

                # Synchronize since we run multiple iterations of this test, to
                # isolate failure hangs.
                torch.cuda.synchronize(device=self.rank)