def _dist_train(self, backward_prefetch=BackwardPrefetch.BACKWARD_PRE):
        rank = self.rank
        orig_get_handle_to_prefetch = _get_handle_to_prefetch
        torch.manual_seed(0)
        policy = ModuleWrapPolicy(
            {nn.TransformerEncoderLayer, nn.TransformerDecoderLayer}
        )
        model = FSDP(
            nn.Transformer(d_model=1024, nhead=8, device=device_type),
            device_id=device_type.type,
            auto_wrap_policy=policy,
            use_orig_params=True,
            backward_prefetch=backward_prefetch,
        )
        optim = torch.optim.SGD(model.parameters(), lr=1e-2)

        # prepare input
        torch.manual_seed(rank + 1)
        src = torch.randn((10, 1, 1024), device=device_type)
        tgt = torch.randn((20, 1, 1024), device=device_type)

        # monkey patch
        all_handle_fqns: list[list[str]] = []

        def patched_get_handle_to_prefetch(*args, **kwargs):
            handle = orig_get_handle_to_prefetch(*args, **kwargs)

            self.assertEqual(
                len(args), 2, "expect _get_handle_to_prefetch(state, current_handle)"
            )
            state = args[0]
            current_handle = args[1]
            training_state = _get_training_state(current_handle)
            if (
                training_state == HandleTrainingState.BACKWARD_PRE
                and state.backward_prefetch == BackwardPrefetch.BACKWARD_PRE
            ) or (
                training_state == HandleTrainingState.BACKWARD_POST
                and state.backward_prefetch == BackwardPrefetch.BACKWARD_POST
            ):
                nonlocal all_handle_fqns
                # FQNs prefixed from the root module
                # state._exec_order_data.param_to_fqn
                fqns = _get_handle_fqns_from_root(state, handle)
                all_handle_fqns.append(fqns)
            return handle

        # flat params from prefetch handle should match
        # DECODER_PARAM_FQNS and ENCODER_PARAM_FQNS
        with patch(
            "torch.distributed.fsdp._runtime_utils._get_handle_to_prefetch",
            patched_get_handle_to_prefetch,
        ):
            for _ in range(NUM_ITERS):
                optim.zero_grad()
                loss = model(src, tgt).sum()
                loss.backward()
                optim.step()
                if backward_prefetch is None:
                    self.assertEqual(len(all_handle_fqns), 0)
                    continue
                elif backward_prefetch == BackwardPrefetch.BACKWARD_PRE:
                    # state._exec_order_data.handles_post_forward_order
                    # equals forward order
                    #     encoder 0...5 -> decoder 0...5 -> root
                    # pre-backward hook order
                    #     root -> decoder 5...0 -> encoder 5...0
                    # prefetch order
                    #     decoder 5...0 -> encoder 5...0 -> None
                    # None: when current_handle=encoder 0,
                    #       _get_handle_to_prefetch returns None
                    # +1 is for the above None
                    encoder_begin_index = ENCODER_BEGIN_INDEX_FOR_PRE
                    self.assertEqual(
                        len(all_handle_fqns), TOTAL_NUM_PREFETCH_FOR_PRE + 1
                    )
                elif backward_prefetch == BackwardPrefetch.BACKWARD_POST:
                    # state._exec_order_data.handles_post_forward_order
                    # equals forward order (same as BACKWARD_PRE)
                    #     encoder 0...5 -> decoder 0...5 -> root
                    # post-backward hook (AccumulateGrad) order
                    #     decoder 5, 4...0 -> encoder 5...0 -> root
                    # prefetch order
                    #     decoder 4...0 -> encoder 5...0 -> None -> None
                    # 1st None: when current_handle=encoder 0,
                    #           _get_handle_to_prefetch returns None
                    # 2nd None: when current_handle=root,
                    #           get decoder 5 inside _get_handle_to_prefetch
                    #           but not needed since decoder 5 is computed already
                    # +2 is for the above Nones
                    encoder_begin_index = ENCODER_BEGIN_INDEX_FOR_POST
                    self.assertEqual(
                        len(all_handle_fqns), TOTAL_NUM_PREFETCH_FOR_POST + 2
                    )

                # ith_prefetch: 0, 1st, 2nd, 3rd, 4th ... ith prefetch
                for ith_prefetch, fqns in enumerate(all_handle_fqns):
                    if ith_prefetch >= 0 and ith_prefetch < encoder_begin_index:
                        layer_index = encoder_begin_index - 1 - ith_prefetch
                        self.assertEqual(
                            fqns,
                            [x.format(index=layer_index) for x in DECODER_PARAM_FQNS],
                        )
                    elif (
                        ith_prefetch >= encoder_begin_index
                        and ith_prefetch <= encoder_begin_index + ENCODER_PREFETCH_NUM
                    ):
                        layer_index = (
                            encoder_begin_index + ENCODER_PREFETCH_NUM - ith_prefetch
                        )
                        self.assertEqual(
                            fqns,
                            [x.format(index=layer_index) for x in ENCODER_PARAM_FQNS],
                        )
                    else:
                        self.assertTrue(fqns is None)

                all_handle_fqns = []