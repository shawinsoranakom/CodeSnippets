def test_cudnn_weight_format(self):
        rnns = [
            nn.LSTM(10, 20, batch_first=True),
            nn.LSTM(10, 20, batch_first=True, proj_size=10),
            nn.GRU(10, 20, batch_first=True),
            nn.RNN(10, 20, batch_first=True)
        ]
        # ROCm RNN does not issue warning about single contig chunk of memory, so don't assert it
        first_warn = not torch.version.hip
        for rnn in rnns:
            rnn.cuda()
            input = torch.randn(5, 4, 10, requires_grad=True, device="cuda")
            hx = torch.randn(1, 5, 20, requires_grad=True, device="cuda")
            all_vars = [input, hx] + list(rnn.parameters())
            if isinstance(rnn, nn.LSTM):
                # LSTM with projections has different hx size
                if rnn.proj_size > 0:
                    hx = torch.randn(1, 5, 10, requires_grad=True, device="cuda")
                    all_vars[1] = hx
                cx = torch.randn(1, 5, 20, requires_grad=True, device="cuda")
                all_vars[2:2] = [cx]
                hx = (hx, cx)

            output = rnn(input, hx)
            output[0].sum().backward()
            grads = [v.grad.data.clone() for v in all_vars]
            for v in all_vars:
                v.grad.data.zero_()

            # Weights will no longer view onto the same chunk of memory
            weight = all_vars[4]
            weight_data = weight.data.clone()
            with torch.no_grad():
                weight.set_(weight_data)

            for _ in range(2):
                with warnings.catch_warnings(record=True) as w:
                    output_noncontig = rnn(input, hx)
                if first_warn:
                    self.assertEqual(len(w), 1)
                    self.assertIn('weights are not part of single contiguous chunk of memory', w[0].message.args[0])
                    first_warn = False
                    warnings.resetwarnings()
                output_noncontig[0].sum().backward()
                grads_noncontig = [v.grad.data.clone() for v in all_vars]
                for v in all_vars:
                    v.grad.data.zero_()
                self.assertEqual(output, output_noncontig)
                self.assertEqual(grads_noncontig, grads)

            # Make sure these still share storage
            weight_data[:] = 4
            self.assertEqual(weight_data, all_vars[4].data)