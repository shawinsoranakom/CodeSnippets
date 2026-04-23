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