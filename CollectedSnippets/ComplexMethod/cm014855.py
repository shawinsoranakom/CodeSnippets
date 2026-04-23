def run(op, kwargs):
            a = torch.randn((size,), device="xpu", dtype=torch.float)

            # Control
            torch.xpu.manual_seed(5)
            eager_out = a
            for _ in range(6):
                eager_out = op(eager_out, **kwargs)

            graph_in = a.clone()
            stream = torch.xpu.Stream()
            stream.wait_stream(torch.xpu.current_stream())
            with torch.xpu.stream(stream):
                torch.xpu.manual_seed(5)

                g = torch.xpu.XPUGraph()
                torch.xpu.empty_cache()
                g.capture_begin()
                graph_out = graph_in
                for _ in range(2):
                    graph_out = op(graph_out, **kwargs)
                g.capture_end()
            torch.xpu.current_stream().wait_stream(stream)

            # Runs a graphed->eager->graphed sequence of RNG ops.
            # replay() plays 2 invocations of the op, so the sequence has 6
            # invocations total, matching Control.
            # replay() reads from graph_in and writes to graph_out.
            g.replay()
            out = op(graph_out, **kwargs)
            out = op(out, **kwargs)
            graph_in.copy_(out)
            g.replay()

            # If replay() updated RNG state correctly, graph_out
            # should now hold data equal to eager_out.
            try:
                self.assertEqual(eager_out, graph_out)
            except Exception as e:
                raise RuntimeError("Failed on ", op) from e

            # Do the same operations varying seeds
            seeds = [6, 128, 9999]

            for seed in seeds:
                torch.xpu.manual_seed(seed)
                graph_in.copy_(a)
                for _ in range(3):
                    g.replay()

                # If the random seed was not updated then the graph would
                # generate the same output as in previous check.
                try:
                    self.assertNotEqual(eager_out, graph_out)
                except Exception as e:
                    raise RuntimeError("Failed on ", op) from e

                # Now repeat the same operations in non-graphed mode.
                torch.xpu.manual_seed(seed)
                for _ in range(3):
                    eager_out.copy_(a)
                    eager_out = op(eager_out, **kwargs)
                    eager_out = op(eager_out, **kwargs)

                # In the end, graph_out and eager_out must be equal
                # as they went under the same set of operations.
                try:
                    self.assertEqual(eager_out, graph_out)
                except Exception as e:
                    raise RuntimeError("Failed on ", op) from e

            # We hold references to all tensors used across streams up til this sync,
            # so no need to call record_stream on those tensors.
            torch.xpu.synchronize()