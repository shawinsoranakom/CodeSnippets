def test_preserve_annotation(self):
        class M(torch.nn.Module):
            def forward(self, x):
                with fx_traceback.annotate({"pp_stage": 0}):
                    with fx_traceback.annotate({"fdsp_bucket": 0}):
                        x = x + 1
                    x = x - 2
                    with fx_traceback.annotate({"cuda_stream": 2, "fsdp_bucket": 1}):
                        x = x * 2
                x = x / 3
                return x

        m = M()

        with fx_traceback.preserve_node_meta():
            ep = export(m, (torch.randn(10),))

        for node in ep.graph.nodes:
            if node.op in ("placeholder", "output"):
                continue
            if node.target == torch.ops.aten.add.Tensor:
                self.assertTrue(node.meta["custom"], {"pp_stage": 0, "fdsp_bucket": 0})
            elif node.target == torch.ops.aten.sub.Tensor:
                self.assertTrue(node.meta["custom"], {"pp_stage": 0})
            elif node.target == torch.ops.aten.mul.Tensor:
                self.assertTrue(
                    node.meta["custom"],
                    {"pp_stage": 0, "cuda_stream": 2, "fsdp_bucket": 1},
                )
            elif node.target == torch.ops.aten.div.Tensor:
                if "custom" in node.meta:
                    self.assertTrue(node.meta["custom"], {})
            else:
                raise AssertionError(f"Node not checked: {node}, {node.target}")