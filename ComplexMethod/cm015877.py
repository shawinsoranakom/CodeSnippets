def _test_lstm_packed(
        self,
        unbatched,
        input_size,
        hidden_size,
        num_layers,
        bidirectional,
        bias,
        empty_state,
        batch_first,
        batch_size,
        seq_len,
        change_input_sizes=False,
    ):
        from torch._dynamo.utils import counters

        dtypes = [torch.float]
        if torch.ops.mkldnn._is_mkldnn_bf16_supported():
            dtypes.append(torch.bfloat16)
        if torch.ops.mkldnn._is_mkldnn_fp16_supported():
            dtypes.append(torch.float16)
        for dtype in dtypes:
            counters.clear()
            num_directions = 2 if bidirectional else 1

            seq_len_var = seq_len + 3
            if unbatched:
                v = torch.randn(seq_len, input_size)
                v_var = torch.randn(seq_len_var, input_size)
                h = torch.randn(num_layers * num_directions, hidden_size)
                c = torch.randn(num_layers * num_directions, hidden_size)
            else:
                if batch_first:
                    v = torch.randn(batch_size, seq_len, input_size)
                    v_var = torch.randn(batch_size, seq_len_var, input_size)
                else:
                    v = torch.randn(seq_len, batch_size, input_size)
                    v_var = torch.randn(seq_len_var, batch_size, input_size)
                h = torch.randn(num_layers * num_directions, batch_size, hidden_size)
                c = torch.randn(num_layers * num_directions, batch_size, hidden_size)

            mod = LstmModule(
                input_size,
                hidden_size,
                num_layers,
                bias,
                bidirectional,
                batch_first,
            ).eval()
            maybe_autocast = (
                torch.cpu.amp.autocast()
                if dtype == torch.bfloat16
                else contextlib.nullcontext()
            )

            with torch.no_grad(), maybe_autocast:
                inps = [v]
                if not empty_state:
                    inps.append((h, c))

                fn_opt = torch.compile(mod, backend="inductor")
                _, code = run_and_get_cpp_code(fn_opt, *inps)

                # Check that _flat_weights are not functional_tensor, otherwise
                # deepcopy will fail during recompilation.
                fn_opt_copy = copy.deepcopy(fn_opt)
                _flat_weights = fn_opt_copy.lstm._flat_weights
                for _flat_weight in _flat_weights:
                    self.assertFalse(torch._is_functional_tensor(_flat_weight))

                self.assertTrue("aten.mkldnn_rnn_layer" in code)
                self.assertEqual(fn_opt(*inps), mod(*inps))
                self.assertEqual(
                    counters["inductor"]["pattern_matcher_count"],
                    num_layers * num_directions
                    + 2,  # num of mkldnn_rnn_layer call + 2 view call on the concatenated hy, cy.
                )

                # Change input sizes
                if change_input_sizes:
                    inps_var = [v_var]
                    self.assertEqual(fn_opt(*inps_var), mod(*inps_var))