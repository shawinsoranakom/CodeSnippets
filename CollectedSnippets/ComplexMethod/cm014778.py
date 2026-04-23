def test_graph_optims_with_explicitly_capturable_param_groups(self):
        # mimicking `_test_graphed_optimizer` maladroitly to pass two param_groups to optimizer.__init__
        n_warmup, n_replay = 3, 2
        for optimizer, second_param_group_capturable in product(
            (
                torch.optim.Adam,
                torch.optim.AdamW,
                torch.optim.ASGD,
                torch.optim.Adamax,
                torch.optim.NAdam,
                torch.optim.RAdam,
                torch.optim.Adadelta,
                torch.optim.RMSprop,
                torch.optim.Rprop,
            ),
            (True, False),
        ):
            ref_p1, param1 = (
                torch.nn.Parameter(torch.ones(1, device="cuda")) for _ in range(2)
            )
            ref_p2, param2 = (
                torch.nn.Parameter(torch.ones(1, device="cuda")) for _ in range(2)
            )
            grads1, grads2 = (
                [torch.randn_like(param1) for _ in range(n_warmup + n_replay)]
                for _ in range(2)
            )
            ref_grads1, ref_grads2 = (
                [t.clone() for t in tensors] for tensors in (grads1, grads2)
            )
            params = [
                {"params": [param1], "capturable": True},
                {"params": [param2], "capturable": second_param_group_capturable},
            ]
            opt = optimizer(params)
            opt_ = optimizer(
                [
                    {"params": [ref_p1], "capturable": False},
                    {"params": [ref_p2], "capturable": False},
                ]
            )

            for i in range(n_warmup + n_replay):
                ref_p1.grad = ref_grads1[i]
                ref_p2.grad = ref_grads2[i]
                opt_.step()

            for i in range(n_warmup):
                param1.grad = grads1[i]
                param2.grad = grads2[i]
                opt.step()

            g = torch.cuda.CUDAGraph()
            if not second_param_group_capturable:
                with self.assertRaisesRegex(RuntimeError, "Attempting CUDA graph"):
                    with torch.cuda.graph(g):
                        opt.step()
            else:
                with torch.cuda.graph(g):
                    opt.step()

                for i in range(n_replay):
                    param1.grad.copy_(grads1[n_warmup + i])
                    param2.grad.copy_(grads2[n_warmup + i])
                    g.replay()
                self.assertEqual(ref_p1, param1)
                self.assertEqual(ref_p2, param2)