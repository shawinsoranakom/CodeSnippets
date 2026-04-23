def test_layer_norm_bwd_req_grad(self):
        device_mesh = self.build_device_mesh()
        batch, seq_len, embedding_dim, vocab_size = 8, 8, 10, 32

        # Test both LayerNorm and RMSNorm (if CUDA)
        norm_types = [torch.nn.LayerNorm]
        if self.device_type == "cuda" and hasattr(torch.nn, "RMSNorm"):
            norm_types.append(torch.nn.RMSNorm)

        # build our subtest configurations and filter out invalid ones
        class SubTest(NamedTuple):
            norm_type: type
            multidim_norm: bool
            elementwise_affine: bool
            emb_req_grad: bool
            ln_req_grad: bool
            out_req_grad: bool

        subtest_fails = {}

        def valid_filter(cfg):
            return not (cfg.ln_req_grad and not cfg.elementwise_affine) and any(cfg[3:])

        subtest_cfgs = list(
            filter(
                valid_filter,
                [
                    SubTest(norm_type, *cfg)
                    for norm_type in norm_types
                    for cfg in itertools.product(*(((False, True),) * 5))
                ],
            )
        )

        for subtest_cfg in subtest_cfgs:
            try:
                (
                    norm_type,
                    multidim_norm,
                    elementwise_affine,
                    emb_req_grad,
                    ln_req_grad,
                    out_req_grad,
                ) = subtest_cfg
                normalized_shape = (
                    (seq_len, embedding_dim) if multidim_norm else (embedding_dim,)
                )

                # configure our local and parallelized models for this subtest
                class LnTpBlock(torch.nn.Module):
                    def __init__(self):
                        super().__init__()
                        self.preln_embeddings = torch.nn.Embedding(
                            vocab_size, embedding_dim
                        )
                        self.layer_norm = norm_type(
                            normalized_shape, elementwise_affine=elementwise_affine
                        )
                        self.postln_linear = torch.nn.Linear(
                            embedding_dim, embedding_dim
                        )

                    def forward(self, tokens):
                        h = self.preln_embeddings(tokens)
                        h = self.layer_norm(h)
                        output = self.postln_linear(h)
                        return output

                parallel_plan = {
                    "preln_embeddings": RowwiseParallel(
                        input_layouts=Replicate(), output_layouts=Shard(1)
                    ),
                    "layer_norm": SequenceParallel(),
                    "postln_linear": ColwiseParallel(
                        input_layouts=Shard(1),
                        output_layouts=Replicate(),
                    ),
                }

                model = LnTpBlock()
                model_local = copy.deepcopy(model).to(device=self.device_type)
                model_dist = parallelize_module(model, device_mesh, parallel_plan)
                req_grad_map = {
                    "preln_embeddings": emb_req_grad,
                    "postln_linear": out_req_grad,
                    "layer_norm": ln_req_grad,
                }

                # apply the relevant `requires_grad` mask for this subtest to both models
                for target_model in [model_local, model_dist]:
                    for n, p in target_model.named_parameters():
                        if not req_grad_map.get(n.rpartition(".")[0], False):
                            p.requires_grad_(False)
                            if p.requires_grad:
                                raise AssertionError(
                                    f"Expected requires_grad to be False for {n}"
                                )
                        else:
                            if not p.requires_grad:
                                raise AssertionError(
                                    f"Expected requires_grad to be True for {n}"
                                )

                # forward step for both local and distributed models
                x = torch.randint(vocab_size, (batch, seq_len), device=self.device_type)
                x_local = x.detach().clone()
                output_local = model_local(x_local)

                with CommDebugMode() as comm_mode:
                    output_dist = model_dist(x)

                output_dist_cmp = (
                    output_dist.full_tensor()
                    if isinstance(output_dist, DTensor)
                    else output_dist
                )
                self.assertEqual(output_local, output_dist_cmp)

                # all requires_grad patterns should have the same forward comm counts
                expected_fwd_comm = {
                    funcol.reduce_scatter_tensor: 1,
                    funcol.all_gather_into_tensor: 2,
                }
                self.assertDictEqual(
                    comm_mode.comm_module_counts["Global"]["forward"], expected_fwd_comm
                )

                # backward step
                output_local.sum().backward()

                with CommDebugMode() as comm_mode:
                    output_dist.sum().backward()

                # ensure gradients (and parameters) remain equal between local and distributed models
                self._check_module(model_local, model_dist, check_grad=True)

                # different requires_grad patterns will have different bwd comm counts
                if out_req_grad and not any((emb_req_grad, ln_req_grad)):
                    expected_bwd_comm = {}
                elif ln_req_grad and not any((emb_req_grad, multidim_norm)):
                    expected_bwd_comm = {funcol.reduce_scatter_tensor: 1}
                elif multidim_norm:
                    expected_bwd_comm = {funcol.all_reduce: 1}
                    expected_bwd_comm[funcol.all_gather_into_tensor] = (
                        2 if emb_req_grad else 1
                    )
                else:
                    expected_bwd_comm = {
                        funcol.reduce_scatter_tensor: 1,
                        funcol.all_gather_into_tensor: 1,
                    }

                self.assertDictEqual(
                    comm_mode.comm_module_counts["Global"]["backward"],
                    expected_bwd_comm,
                )
                output_dist_cmp = (
                    output_dist.full_tensor()
                    if isinstance(output_dist, DTensor)
                    else output_dist
                )
                self.assertEqual(output_local, output_dist_cmp)

            except Exception as e:
                subtest_fails[subtest_cfg] = e
        # if any subtest fails, provide the failed subtests and report the overall failure
        if subtest_fails:
            raise AssertionError(
                f"{len(subtest_fails)}/{len(subtest_cfgs)} subtests failed: {pformat(subtest_fails)}"
            )