def test_averaged_model_exponential(self, use_multi_avg_fn, use_buffers):
        # Test AveragedModel with EMA as avg_fn and use_buffers as True.
        dnn = torch.nn.Sequential(
            torch.nn.Conv2d(1, 5, kernel_size=3),
            torch.nn.BatchNorm2d(5, momentum=0.3),
            torch.nn.Linear(5, 10),
        )
        decay = 0.9

        if use_multi_avg_fn:
            averaged_dnn = AveragedModel(
                dnn, multi_avg_fn=get_ema_multi_avg_fn(decay), use_buffers=use_buffers
            )
        else:

            def avg_fn(p_avg, p, n_avg):
                return decay * p_avg + (1 - decay) * p

            averaged_dnn = AveragedModel(dnn, avg_fn=avg_fn, use_buffers=use_buffers)

        if use_buffers:
            dnn_params = list(itertools.chain(dnn.parameters(), dnn.buffers()))
        else:
            dnn_params = list(dnn.parameters())

        averaged_params = [
            torch.zeros_like(param)
            for param in dnn_params
            if param.size() != torch.Size([])
        ]

        n_updates = 10
        for i in range(n_updates):
            updated_averaged_params = []
            for p, p_avg in zip(dnn_params, averaged_params):
                if p.size() == torch.Size([]):
                    continue
                p.detach().add_(torch.randn_like(p))
                if i == 0:
                    updated_averaged_params.append(p.clone())
                else:
                    updated_averaged_params.append(
                        (p_avg * decay + p * (1 - decay)).clone()
                    )
            averaged_dnn.update_parameters(dnn)
            averaged_params = updated_averaged_params

        if use_buffers:
            for p_avg, p_swa in zip(
                averaged_params,
                itertools.chain(
                    averaged_dnn.module.parameters(), averaged_dnn.module.buffers()
                ),
            ):
                self.assertEqual(p_avg, p_swa)
        else:
            for p_avg, p_swa in zip(averaged_params, averaged_dnn.parameters()):
                self.assertEqual(p_avg, p_swa)
            for b_avg, b_swa in zip(dnn.buffers(), averaged_dnn.module.buffers()):
                self.assertEqual(b_avg, b_swa)