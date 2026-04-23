def check_lengths(lengths, enforce_sorted, use_default_hiddens, proj_size):
            input_size = 3
            hidden_size = 4
            num_layers = 2
            bidirectional = True

            max_length = max(lengths)
            x_leaf = torch.randn(max_length, len(lengths), input_size, device=device,
                                 dtype=dtype, requires_grad=True)
            num_directions = 2 if bidirectional else 1
            lstm = nn.LSTM(input_size, hidden_size, bidirectional=bidirectional,
                           num_layers=num_layers, proj_size=proj_size).to(device, dtype)
            lstm2 = deepcopy(lstm).to(device, dtype)
            x = x_leaf

            hidden0 = None
            if not use_default_hiddens:
                real_hidden_size = hidden_size if proj_size == 0 else proj_size
                hidden0 = (torch.randn(num_directions * num_layers, len(lengths), real_hidden_size,
                                       device=device, dtype=dtype),
                           torch.randn(num_directions * num_layers, len(lengths), hidden_size,
                                       device=device, dtype=dtype))

            # Compute sequences separately
            seq_outs = []
            seq_hiddens = []
            for i, l in enumerate(lengths):
                hidden_i = maybe_index_tuple(hidden0, i)
                out, hid = lstm2(x[:l, i:i + 1], hidden_i)
                out_pad = pad(out, max_length)
                seq_outs.append(out_pad)
                seq_hiddens.append(hid)
            seq_out = torch.cat(seq_outs, 1)
            seq_hidden = tuple(torch.cat(hids, 1) for hids in zip(*seq_hiddens))

            # Use packed format
            packed = rnn_utils.pack_padded_sequence(x, lengths, enforce_sorted=enforce_sorted)
            packed_out, packed_hidden = lstm(packed, hidden0)
            unpacked, unpacked_len = rnn_utils.pad_packed_sequence(packed_out)

            # Check forward
            prec = dtype2prec_DONTUSE[dtype]
            self.assertEqual(packed_hidden, seq_hidden, atol=prec, rtol=0)
            self.assertEqual(unpacked, seq_out, atol=prec, rtol=0)
            self.assertEqual(unpacked_len, lengths, atol=prec, rtol=0)

            # Check backward
            seq_out.sum().backward()
            grad_x = x_leaf.grad.data.clone()
            x_leaf.grad.data.zero_()
            unpacked.sum().backward()

            self.assertEqual(x_leaf.grad, grad_x, atol=dtype2prec_DONTUSE[dtype], rtol=0)
            for p1, p2 in zip(lstm.parameters(), lstm2.parameters()):
                prec = dtype2prec_DONTUSE[dtype]
                if dtype == torch.float16:
                    prec = 4e-2
                elif dtype == torch.float32:
                    prec = 2e-4
                self.assertEqual(p1.grad, p2.grad, atol=prec, rtol=0)