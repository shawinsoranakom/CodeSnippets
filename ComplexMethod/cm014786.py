def test_autocast_rnn(self):
        with torch.backends.cudnn.flags(enabled=True, deterministic=True):
            # seq, batch, features, hidden size
            clses = ("RNN", "GRU", "LSTM")
            T, B, F, H = 3, 4, 5, 6
            dtypes = (torch.float16, torch.float32)
            input_layouts = ("seq_first", "batch_first", "packed")

            for (
                cls,
                num_layers,
                bias,
                input_layout,
                bidirectional,
                try_nonpreflattened_weights,
                input_dtype,
                hidden_dtype,
                weight_dtype,
            ) in product(
                clses,
                (1, 2),
                (True, False),
                input_layouts,
                (True, False),
                (True, False),
                dtypes,
                dtypes,
                dtypes,
            ):
                if input_layout == "seq_first":
                    batch_first = False
                    x = torch.randn((T, B, F), device="cuda", dtype=input_dtype)
                elif input_layout == "batch_first":
                    batch_first = True
                    x = torch.randn((B, T, F), device="cuda", dtype=input_dtype)
                elif input_layout == "packed":
                    batch_first = False
                    x = torch.nn.utils.rnn.pack_padded_sequence(
                        torch.randn((T, B, F), device="cuda", dtype=input_dtype),
                        lengths=(3, 2, 1, 3),
                        enforce_sorted=False,
                    )

                rnn = (
                    getattr(torch.nn, cls)(
                        F,
                        H,
                        num_layers=num_layers,
                        bidirectional=bidirectional,
                        bias=bias,
                        batch_first=batch_first,
                    )
                    .cuda()
                    .to(dtype=weight_dtype)
                )

                if try_nonpreflattened_weights:
                    for p in rnn.parameters():
                        with torch.no_grad():
                            p.set_(p.clone())

                h = torch.randn(
                    (num_layers * (2 if bidirectional else 1), B, H),
                    device="cuda",
                    dtype=hidden_dtype,
                )
                if cls == "LSTM":
                    c = torch.randn(
                        (num_layers * (2 if bidirectional else 1), B, H),
                        device="cuda",
                        dtype=hidden_dtype,
                    )
                    h = (h, c)

                with torch.autocast("cuda"):
                    out, h_out = rnn(x, h)
                out = out.data if input_layout == "packed" else out
                self.assertEqual(out.dtype, torch.float16)
                # Autocast wrapper requires at::_cudnn_rnn is autograd-exposed.  This check can't guarantee
                # at::_cudnn_rnn is autograd-exposed, but if it fires, it indicates some funny business has
                # occurred and we should double check that at::_cudnn_rnn remains autograd-exposed.
                self.assertEqual(
                    out.grad_fn.name(),
                    "MiopenRnnBackward0" if torch.version.hip else "CudnnRnnBackward0",
                )
                out.sum().backward()
                grads = [p.grad.clone() for p in rnn.parameters()]

                rnn.zero_grad()

                if cls == "LSTM":
                    out_control, h_out_control = rnn.to(dtype=torch.float16)(
                        x.half(), (h[0].half(), h[1].half())
                    )
                else:
                    out_control, h_out_control = rnn.to(dtype=torch.float16)(
                        x.half(), h.half()
                    )
                out_control = (
                    out_control.data if input_layout == "packed" else out_control
                )
                out_control.sum().backward()
                grads_control = [p.grad.clone() for p in rnn.parameters()]

                # Compares with default tolerances, even for FP16 execution.  Barring nondeterminism,
                # autocast and control results should be bitwise identical.
                self.assertEqual(out, out_control)

                if cls == "LSTM":
                    self.assertTrue(
                        h_out[0].dtype is torch.float16
                        and h_out[1].dtype is torch.float16
                    )
                    self.assertEqual(h_out[0], h_out_control[0])
                    self.assertEqual(h_out[1], h_out_control[1])
                else:
                    self.assertEqual(h_out.dtype, torch.float16)
                    self.assertEqual(h_out, h_out_control)
                for grad, grad_control in zip(grads, grads_control):
                    self.assertEqual(grad.half(), grad_control)