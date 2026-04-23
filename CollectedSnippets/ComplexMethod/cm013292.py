def _validate_execution_trace_nccl(self, et_file: str) -> None:
            """Torch profiler includes nccl metadata in an inserted operator called "record_param_comms"
            We test for basic fields in these nodes in the Execution Trace.
            """
            with open(et_file) as f:
                et = json.load(f)
            pg_cfg_node = [
                n for n in et["nodes"] if n["name"] == "## process_group:init ##"
            ]
            self.assertGreaterEqual(len(pg_cfg_node), 1)
            nccl_meta_nodes = [
                n for n in et["nodes"] if n["name"] == "record_param_comms"
            ]
            self.assertEqual(len(nccl_meta_nodes), 3)
            per_coll_meta = defaultdict(list)

            # Sanity check NCCL metadata nodes
            for n in nccl_meta_nodes:
                attrs_list = n.get("attrs", [])
                self.assertGreater(len(attrs_list), 0)
                attrs = {a["name"]: a["value"] for a in attrs_list}

                collname = attrs.get("collective_name", "")
                self.assertNotEqual(collname, "")
                self.assertNotEqual(attrs.get("dtype", ""), "")

                per_coll_meta[collname].append(attrs)
                if collname == "wait":
                    continue

                self.assertEqual(attrs["pg_name"], "0")  # yes this is a string
                self.assertEqual(attrs["pg_desc"], "default_pg")
                self.assertEqual(attrs["pg_size"], 2)

                self.assertGreaterEqual(attrs.get("in_msg_nelems", -1), 0)
                self.assertGreaterEqual(attrs.get("out_msg_nelems", -1), 0)
                self.assertTrue("in_split_size" in attrs)
                self.assertTrue("out_split_size" in attrs)
                self.assertEqual(attrs.get("global_rank_start", -1), 0)
                self.assertEqual(attrs.get("global_rank_stride", -1), 1)

            # print(per_coll_meta)
            self.assertEqual(len(per_coll_meta["allreduce"]), 2)
            self.assertEqual(len(per_coll_meta["wait"]), 1)

            # check allreduce message sizes
            a0 = per_coll_meta["allreduce"][0]
            self.assertEqual(a0["out_msg_nelems"], 100, msg=f"{a0}")
            self.assertEqual(a0["dtype"], "Float", msg=f"{a0}")
            a1 = per_coll_meta["allreduce"][1]
            self.assertEqual(a1["out_msg_nelems"], 1, msg=f"{a1}")
            self.assertEqual(a1["dtype"], "Int", msg=f"{a1}")