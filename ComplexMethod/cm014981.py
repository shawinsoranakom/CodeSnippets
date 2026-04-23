def test_lstm(self):
        seed = 2023
        torch.manual_seed(seed)

        params_list = self._lstm_params_list()
        for dtype in types:
            bf16 = dtype == torch.bfloat16
            fp16 = dtype == torch.half
            rtol = 1.3e-6
            atol = 1e-5

            if bf16:
                rtol = 0.02
                atol = 0.02
            if fp16:
                rtol = 1e-3
                atol = 1e-3
            for input_size, hidden_size, num_layers, bidirectional, bias, batch_first, dropout, batch_size, seq_len, training \
                    in itertools.product(*params_list):
                num_directions = 2 if bidirectional else 1
                if batch_first:
                    input = torch.randn(batch_size, seq_len, input_size, dtype=torch.float32)
                else:
                    input = torch.randn(seq_len, batch_size, input_size, dtype=torch.float32)
                h = torch.randn(num_layers * num_directions, batch_size, hidden_size, dtype=torch.float32)
                c = torch.randn(num_layers * num_directions, batch_size, hidden_size, dtype=torch.float32)
                if fp16:
                    # TODO add training support when oneDNN support lstm FP16 training
                    training = False
                model = torch.nn.LSTM(input_size, hidden_size, num_layers, bidirectional=bidirectional,
                                      bias=bias, dropout=dropout, batch_first=batch_first).float()
                model.train() if training else model.eval()
                input1 = input.clone().requires_grad_(training)
                input2 = input.clone().requires_grad_(training)

                h1 = h.clone().requires_grad_(training)
                h2 = h.clone().requires_grad_(training)
                c1 = c.clone().requires_grad_(training)
                c2 = c.clone().requires_grad_(training)

                model1 = copy.deepcopy(model)
                model2 = copy.deepcopy(model)
                with torch.no_grad() if not training else nullcontext():
                    with torch.backends.mkldnn.flags(enabled=False):
                        torch.manual_seed(seed)
                        output1, (hn1, cn1) = self._cast_dtype(model1, dtype)(
                            self._cast_dtype(input1, dtype),
                            (
                                self._cast_dtype(h1, dtype),
                                self._cast_dtype(c1, dtype),
                            ),
                        )

                    torch.manual_seed(seed)
                    output2, (hn2, cn2) = self._cast_dtype(model2, dtype)(
                        self._cast_dtype(input2, dtype),
                        (
                            self._cast_dtype(h2, dtype),
                            self._cast_dtype(c2, dtype),
                        ),
                    )
                    self.assertEqual(output1, output2, rtol=rtol, atol=atol)
                    self.assertEqual(hn1, hn2, rtol=rtol, atol=atol)
                    self.assertEqual(cn1, cn2, rtol=rtol, atol=atol)

                    if training:
                        with torch.backends.mkldnn.flags(enabled=False):
                            torch.manual_seed(seed)
                            output1.sum().backward(retain_graph=True)

                        torch.manual_seed(seed)
                        output2.sum().backward(retain_graph=True)

                        self.assertEqual(input1.grad, input2.grad, rtol=rtol, atol=atol)
                        for name, para in model1.named_parameters():
                            self.assertEqual(para, getattr(model2, name))
                            self.assertEqual(
                                para.grad,
                                getattr(model2, name).grad,
                                rtol=rtol,
                                atol=atol,
                            )

                        with torch.backends.mkldnn.flags(enabled=False):
                            torch.manual_seed(seed)
                            hn1.sum().backward(retain_graph=True)
                        torch.manual_seed(seed)
                        hn2.sum().backward(retain_graph=True)
                        self.assertEqual(h1.grad, h2.grad, rtol=rtol, atol=atol)

                        with torch.backends.mkldnn.flags(enabled=False):
                            torch.manual_seed(seed)
                            cn1.sum().backward(retain_graph=True)
                        torch.manual_seed(seed)
                        cn2.sum().backward(retain_graph=True)
                        self.assertEqual(c1.grad, c2.grad, rtol=rtol, atol=atol)