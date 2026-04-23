def test_profiler_fwd_bwd_link(self):
        with _profile(use_kineto=True) as prof:
            t1, t2 = (
                torch.ones(1, requires_grad=True),
                torch.ones(1, requires_grad=True),
            )
            z = torch.add(t1, t2)
            y = torch.ones(1)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(z, y)
            loss.backward()
        with TemporaryFileName(mode="w+") as fname:
            prof.export_chrome_trace(fname)
            with open(fname) as f:
                j = json.load(f)
                events = j["traceEvents"]
                ts_to_name = {}
                flow_s_to_ts = {}
                flow_f_to_ts = {}
                for e in events:
                    if e["ph"] == "X":
                        ts_to_name[e["ts"]] = e["name"]
                    if (
                        "cat" in e
                        and "name" in e
                        and e["cat"] == "fwdbwd"
                        and e["name"] == "fwdbwd"
                    ):
                        if e["ph"] == "s":
                            flow_s_to_ts[e["id"]] = e["ts"]
                        elif e["ph"] == "f":
                            flow_f_to_ts[e["id"]] = e["ts"]

                self.assertEqual(len(flow_s_to_ts), 2)
                self.assertEqual(len(flow_f_to_ts), 2)
                self.assertIn(1, flow_s_to_ts)
                self.assertIn(1, flow_f_to_ts)
                self.assertIn(2, flow_s_to_ts)
                self.assertIn(2, flow_f_to_ts)
                s_ts_1 = flow_s_to_ts[1]
                f_ts_1 = flow_f_to_ts[1]
                s_ts_2 = flow_s_to_ts[2]
                f_ts_2 = flow_f_to_ts[2]
                self.assertTrue(
                    all(ts in ts_to_name for ts in [s_ts_1, f_ts_1, s_ts_2, f_ts_2])
                )
                self.assertTrue(
                    ts_to_name[s_ts_1] == "aten::binary_cross_entropy_with_logits"
                )
                self.assertTrue(ts_to_name[s_ts_2] == "aten::add")