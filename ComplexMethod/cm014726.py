def _test_RNN_cpu_vs_cudnn(self, dropout, dtype=torch.double):

        def forward_backward(cuda, rnn, input_val, grad_output, weights_val, hx_val, grad_hy,
                             cx_val=None, grad_cy=None):
            is_lstm = isinstance(rnn, nn.LSTM)

            for x_layer, y_layer in zip(rnn.all_weights, weights_val):
                for x, y in zip(x_layer, y_layer):
                    x.data.copy_(y.data)

            if isinstance(input_val, rnn_utils.PackedSequence):
                input = rnn_utils.PackedSequence(
                    input_val.data.data.requires_grad_(True), input_val.batch_sizes)
                input_var = input.data
            else:
                input = input_val.clone().requires_grad_(True)
                input_var = input
            if is_lstm:
                if cx_val is None:
                    hx = (hx_val.clone().requires_grad_(True),
                          hx_val.add(1).requires_grad_(True))
                else:
                    hx = (hx_val.clone().requires_grad_(True),
                          cx_val.add(1).requires_grad_(True))
            else:
                hx = hx_val.clone().requires_grad_(True)

            if cuda:
                rnn.cuda()
                input_var.data = input_var.data.cuda()
                if is_lstm:
                    hx[0].data = hx[0].data.cuda()
                    hx[1].data = hx[1].data.cuda()
                else:
                    hx.data = hx.data.cuda()
                grad_hy = grad_hy.cuda()
                if grad_cy is not None:
                    grad_cy = grad_cy.cuda()
                grad_output = grad_output.cuda()

            output, hy = rnn(input, hx)

            if isinstance(output, rnn_utils.PackedSequence):
                output = output.data

            if is_lstm:
                if grad_cy is None:
                    torch.autograd.backward([output, hy[0], hy[1]], [grad_output, grad_hy, grad_hy + 1])
                else:
                    torch.autograd.backward([output, hy[0], hy[1]], [grad_output, grad_hy, grad_cy + 1])
            else:
                torch.autograd.backward([output, hy], [grad_output, grad_hy])

            return {'output': output.data,
                    'hy': hy[0].data if is_lstm else hy.data,
                    'weights': rnn.all_weights,
                    'grad_input': input_var.grad.data,
                    'grad_hx': hx[0].grad.data if is_lstm else hx.grad.data,
                    'cy': hy[1].data if is_lstm else None,
                    'grad_cx': hx[1].grad.data if is_lstm else None}

        input_size = 10
        hidden_size = 6
        proj_size = 3
        num_layers = 2
        seq_length = 7
        batch = 6

        def make_noncontig(tensor):
            ndim = tensor.dim()
            return torch.stack([tensor.clone().zero_(), tensor], ndim).select(ndim, 1)

        def compare_cpu_gpu(outputs_cpu, outputs_gpu):
            self.assertEqual(list(outputs_cpu.keys()), list(outputs_gpu.keys()))
            for key in outputs_cpu:
                if key != 'weights':
                    self.assertEqual(outputs_cpu[key], outputs_gpu[key], atol=5e-5, rtol=0, msg=key)

            # check grad weights separately, as nested dict
            for cpu_layer_weight, gpu_layer_weight in zip(outputs_cpu['weights'], outputs_gpu['weights']):
                for (cpu_weight, gpu_weight) in zip(cpu_layer_weight, gpu_layer_weight):
                    self.assertEqual(cpu_weight.grad.data, gpu_weight.grad.data, atol=5e-5, rtol=0)

        for module in (nn.RNN, nn.LSTM, nn.GRU):
            for bias, bidirectional, batch_first, contig, variable_len, lens_as_tensor \
                    in product((True, False), repeat=6):

                num_directions = 2 if bidirectional else 1
                if batch_first:
                    input_val = torch.randn(batch, seq_length, input_size, dtype=dtype)
                    grad_output = torch.randn(batch, seq_length, hidden_size * num_directions, dtype=dtype)
                else:
                    input_val = torch.randn(seq_length, batch, input_size, dtype=dtype)
                    grad_output = torch.randn(seq_length, batch, hidden_size * num_directions, dtype=dtype)

                hx_val = torch.randn(num_layers * num_directions, batch, hidden_size, dtype=dtype)
                grad_hy = torch.randn(num_layers * num_directions, batch, hidden_size, dtype=dtype)

                if not contig:
                    grad_output = make_noncontig(grad_output)
                    grad_hy = make_noncontig(grad_hy)
                    input_var = make_noncontig(input_val)
                    hx_val = make_noncontig(hx_val)

                if variable_len:
                    lengths = [7, 5, 5, 2, 1, 1]
                    if lens_as_tensor:
                        lengths = torch.tensor(lengths, dtype=torch.long)
                    input_val = rnn_utils.pack_padded_sequence(input_val, lengths, batch_first=batch_first)
                    grad_output = rnn_utils.pack_padded_sequence(grad_output, lengths, batch_first=batch_first).data

                rnn = module(input_size,
                             hidden_size,
                             num_layers,
                             bias=bias,
                             dropout=dropout,
                             bidirectional=bidirectional,
                             batch_first=batch_first).to(dtype)

                outputs_cpu = forward_backward(
                    False, rnn, input_val, grad_output, rnn.all_weights, hx_val, grad_hy)

                rnn_gpu = module(input_size,
                                 hidden_size,
                                 num_layers,
                                 bias=bias,
                                 dropout=dropout,
                                 bidirectional=bidirectional,
                                 batch_first=batch_first).to(dtype)

                outputs_gpu = forward_backward(
                    True, rnn_gpu, input_val, grad_output, rnn.all_weights, hx_val, grad_hy)

                compare_cpu_gpu(outputs_cpu, outputs_gpu)

        for nonlinearity in ('tanh', 'relu'):
            hx_val = torch.randn(num_layers, batch, hidden_size, dtype=dtype)
            input_val = torch.randn(seq_length, batch, input_size, dtype=dtype)
            grad_output = torch.randn(
                seq_length, batch, hidden_size * num_directions, dtype=dtype)
            grad_hy = torch.randn(
                num_layers * num_directions, batch, hidden_size, dtype=dtype)

            rnn = nn.RNN(input_size, hidden_size, num_layers, bias=bias, nonlinearity=nonlinearity).to(dtype)
            outputs_cpu = forward_backward(False, rnn, input_val, grad_output, rnn.all_weights, hx_val, grad_hy)

            rnn_gpu = nn.RNN(input_size, hidden_size, num_layers, bias=bias, nonlinearity=nonlinearity).to(dtype)
            outputs_gpu = forward_backward(True, rnn_gpu, input_val, grad_output, rnn.all_weights, hx_val, grad_hy)

            compare_cpu_gpu(outputs_cpu, outputs_gpu)

        # checking LSTM with projections
        for bias, bidirectional, batch_first, contig, variable_len, lens_as_tensor \
                in product((True, False), repeat=6):
            num_directions = 2 if bidirectional else 1
            if batch_first:
                input_val = torch.randn(batch, seq_length, input_size, dtype=dtype)
                grad_output = torch.randn(batch, seq_length, proj_size * num_directions, dtype=dtype)
            else:
                input_val = torch.randn(seq_length, batch, input_size, dtype=dtype)
                grad_output = torch.randn(seq_length, batch, proj_size * num_directions, dtype=dtype)

            hx_val = torch.randn(num_layers * num_directions, batch, proj_size, dtype=dtype)
            cx_val = torch.randn(num_layers * num_directions, batch, hidden_size, dtype=dtype)
            grad_hy = torch.randn(num_layers * num_directions, batch, proj_size, dtype=dtype)
            grad_cy = torch.randn(num_layers * num_directions, batch, hidden_size, dtype=dtype)

            if not contig:
                grad_output = make_noncontig(grad_output)
                grad_hy = make_noncontig(grad_hy)
                grad_cy = make_noncontig(grad_cy)
                input_var = make_noncontig(input_val)
                hx_val = make_noncontig(hx_val)
                cx_val = make_noncontig(cx_val)

            if variable_len:
                lengths = [7, 5, 5, 2, 1, 1]
                if lens_as_tensor:
                    lengths = torch.tensor(lengths, dtype=torch.long)
                input_val = rnn_utils.pack_padded_sequence(input_val, lengths, batch_first=batch_first)
                grad_output = rnn_utils.pack_padded_sequence(grad_output, lengths, batch_first=batch_first).data

            rnn = nn.LSTM(input_size,
                          hidden_size,
                          num_layers,
                          bias=bias,
                          dropout=dropout,
                          bidirectional=bidirectional,
                          batch_first=batch_first,
                          proj_size=proj_size).to(dtype)

            outputs_cpu = forward_backward(
                False, rnn, input_val, grad_output, rnn.all_weights,
                hx_val, grad_hy, cx_val, grad_cy)

            rnn_gpu = nn.LSTM(input_size,
                              hidden_size,
                              num_layers,
                              bias=bias,
                              dropout=dropout,
                              bidirectional=bidirectional,
                              batch_first=batch_first,
                              proj_size=proj_size).to(dtype)

            outputs_gpu = forward_backward(
                True, rnn_gpu, input_val, grad_output, rnn.all_weights,
                hx_val, grad_hy, cx_val, grad_cy)
            compare_cpu_gpu(outputs_cpu, outputs_gpu)