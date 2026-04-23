def test_aot_sequence_nr(self):
        class Model(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv1 = torch.nn.Conv2d(
                    in_channels=16,
                    out_channels=16,
                    kernel_size=(1, 1),
                    stride=1,
                    padding="same",
                    bias=True,
                )
                self.bn1 = torch.nn.BatchNorm2d(num_features=16)
                self.relu1 = torch.nn.ReLU()
                self.fc1 = torch.nn.Linear(in_features=1638400, out_features=1)
                self.loss_fn = torch.nn.L1Loss()

            def forward(self, x, target):
                y = x
                x = self.conv1(x)
                x = self.bn1(x)
                x = self.relu1(x)
                x = x + y
                x = torch.flatten(x)
                x = self.fc1(x)
                output = self.loss_fn(x, target)

                return (output,)

        mod = Model()
        mod.train()
        x = torch.rand(100, 16, 32, 32, requires_grad=True)
        target = torch.rand(1)

        # Use dynamo export to get the fx graph module
        g_mod, _ = torch._dynamo.export(mod, x, target)

        def _prepare_model_args():
            named_parameters = dict(g_mod.named_parameters(remove_duplicate=False))
            named_buffers = dict(g_mod.named_buffers(remove_duplicate=False))
            params_and_buffers = {
                **dict(named_parameters),
                **dict(named_buffers),
            }
            params_and_buffers_flat, params_spec = pytree.tree_flatten(
                params_and_buffers
            )
            params_len = len(params_and_buffers_flat)
            functional_call = create_functional_call(g_mod, params_spec, params_len)
            return params_and_buffers_flat, functional_call

        full_args, fn_to_trace = _prepare_model_args()
        param_and_buf_len = len(full_args)
        full_args.extend([x, target])

        # aot_export requires a graph mod input of fwd graph
        # returns the full fwd/bwd graph in graph mod format
        with torch.enable_grad(), fx_traceback.preserve_node_meta():
            fx_g, _, _, _ = _aot_export_function(
                fn_to_trace,
                full_args,
                decompositions=None,
                num_params_buffers=param_and_buf_len,
                no_tangents=True,
            )

        # Walk all the nodes in fx graph.
        # Write the resulting ops to a table
        min_seq_nr = -1
        seq_table = "SeqNr|OrigAten|SrcFn|FwdSrcFn\n"
        for node in fx_g.graph.nodes:
            if "call_" in node.op and "getitem" not in str(node.target):
                seq_nr = node.meta.get("seq_nr", -1)
                if seq_nr < 0:
                    continue
                if min_seq_nr < 0:
                    min_seq_nr = seq_nr
                source_fn_stack = node.meta.get("source_fn_stack", [])
                orig_aten = node.meta.get("original_aten", "")
                mod_name = ""
                if len(source_fn_stack) > 0:
                    mod_name = source_fn_stack[-1][0]
                # Make all seq_nr relative so it starts at 0
                seq_nr = seq_nr - min_seq_nr
                # For backward nodes, also test that metadata from the corresponding
                # forward node is copied over.
                fwd_source_fn_stack = node.meta.get("fwd_source_fn_stack", [])
                fwd_mod_name = ""
                if len(fwd_source_fn_stack):
                    fwd_mod_name = fwd_source_fn_stack[-1][0]
                seq_table = (
                    seq_table + f"{seq_nr}|{orig_aten}|{mod_name}|{fwd_mod_name}\n"
                )

        self.maxDiff = None
        self.assertExpectedInline(
            seq_table,
            dedent(
                """\
SeqNr|OrigAten|SrcFn|FwdSrcFn
0|aten.convolution.default|conv2d|
0|aten.add.Tensor|add_|
1|aten._native_batch_norm_legit_functional.default|batch_norm|
2|aten.relu.default|relu|
2|aten.detach.default|relu|
3|aten.add.Tensor|add|
4|aten.view.default|flatten|
5|aten.view.default|linear|
6|aten.t.default|linear|
7|aten.addmm.default|linear|
8|aten.view.default|linear|
9|aten.sub.Tensor|l1_loss|
10|aten.abs.default|l1_loss|
11|aten.mean.default|l1_loss|
11|aten.ones_like.default||l1_loss
11|aten.expand.default||l1_loss
11|aten.div.Scalar||l1_loss
10|aten.sgn.default||l1_loss
10|aten.mul.Tensor||l1_loss
8|aten.view.default||linear
7|aten.t.default||linear
7|aten.mm.default||linear
7|aten.t.default||linear
7|aten.mm.default||linear
7|aten.t.default||linear
7|aten.sum.dim_IntList||linear
7|aten.view.default||linear
6|aten.t.default||linear
5|aten.view.default||linear
4|aten.view.default||flatten
2|aten.detach.default||relu
2|aten.threshold_backward.default||relu
1|aten.native_batch_norm_backward.default||batch_norm
0|aten.convolution_backward.default||conv2d
11|aten.add.Tensor||
"""
            ),
        )