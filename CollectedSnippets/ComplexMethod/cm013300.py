def _test_output_unused_in_loss(self, module_cls, gradient_as_bucket_view):
            model = module_cls()
            local_net = copy.deepcopy(model)
            net = torch.nn.parallel.DistributedDataParallel(
                copy.deepcopy(model).cuda(self.rank),
                device_ids=[self.rank],
                find_unused_parameters=True,
            )

            # Tests that certain parameters not getting gradient since the
            # output is unused in loss computation is supported. Specifically,
            # checks that the grads remain unchanged and are the same as local
            # training.
            inp = torch.randn(10, 10)

            # Ensure that if a param is not used in loss computation, its
            # gradient is untouched, i.e. if it is None before it is None after,
            # not zero.
            if module_cls == DictOutputModule:
                a, b = local_net(inp)["predictions"]
                a_dist, b_dist = net(inp)["predictions"]
            else:
                a, b = local_net(inp)
                a_dist, b_dist = net(inp)

            loss_dist = b_dist.sum()
            loss_dist.backward()

            # Ensure that gradient corresponding to parameter "a" was not
            # touched, i.e. it is None and matches the local grad.
            if module_cls == DictOutputModule:
                self.assertTrue(net.module.module.a.weight.grad is None)
                self.assertEqual(
                    net.module.module.a.weight.grad, local_net.module.a.weight.grad
                )
            else:
                self.assertTrue(net.module.a.weight.grad is None)
                self.assertEqual(net.module.a.weight.grad, local_net.a.weight.grad)

            saved_a_local_grad = None
            saved_a_dist_grad = None
            net.zero_grad()
            local_net.zero_grad()
            for i in range(6):
                if module_cls == DictOutputModule:
                    a, b = local_net(inp)["predictions"]
                    a_dist, b_dist = net(inp)["predictions"]
                else:
                    a, b = local_net(inp)
                    a_dist, b_dist = net(inp)
                if i < 2:
                    # Use both params in loss computation. Later, "a" will go
                    # unused and we check to ensure DDP supports this and
                    # gradients remain the same as local training.
                    t = a @ b
                    t_dist = a_dist @ b_dist
                    loss = t.sum()
                    loss_dist = t_dist.sum()
                else:
                    # Model output "a" unused in loss.
                    loss = b.sum()
                    loss_dist = b_dist.sum()
                loss.backward()
                loss_dist.backward()
                if i == 1:
                    # Save grads to compare with them in next iterations.
                    if module_cls == DictOutputModule:
                        saved_a_local_grad = local_net.module.a.weight.grad
                        saved_a_dist_grad = net.module.module.a.weight.grad
                    else:
                        saved_a_local_grad = local_net.a.weight.grad
                        saved_a_dist_grad = net.module.a.weight.grad
                    self.assertEqual(saved_a_local_grad, saved_a_dist_grad)
                elif i >= 2:
                    # parameter "a" of both models should be the same and not change
                    if module_cls == DictOutputModule:
                        self.assertEqual(
                            net.module.module.a.weight.grad, saved_a_dist_grad
                        )
                        self.assertEqual(
                            local_net.module.a.weight.grad, saved_a_local_grad
                        )
                    else:
                        self.assertEqual(net.module.a.weight.grad, saved_a_dist_grad)
                        self.assertEqual(local_net.a.weight.grad, saved_a_local_grad)

                # Verify grads are the same
                for local_param, dist_param in zip(
                    local_net.parameters(), net.parameters(), strict=True
                ):
                    local_grad = local_param.grad
                    dist_grad = dist_param.grad
                    self.assertEqual(local_grad, dist_grad)

            dist.barrier()