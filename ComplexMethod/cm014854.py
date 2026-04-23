def _check_memory_stat_consistency():
            snapshot = torch.xpu.memory_snapshot()

            expected_each_device = collections.defaultdict(
                lambda: collections.defaultdict(int)
            )

            for segment in snapshot:
                expandable = segment["is_expandable"]
                expected = expected_each_device[segment["device"]]
                pool_str = segment["segment_type"] + "_pool"

                if not expandable:
                    expected["segment.all.current"] += 1
                    expected[f"segment.{pool_str}.current"] += 1

                expected["allocated_bytes.all.current"] += segment["allocated_size"]
                expected[f"allocated_bytes.{pool_str}.current"] += segment[
                    "allocated_size"
                ]

                expected["reserved_bytes.all.current"] += segment["total_size"]
                expected[f"reserved_bytes.{pool_str}.current"] += segment["total_size"]

                expected["active_bytes.all.current"] += segment["active_size"]
                expected[f"active_bytes.{pool_str}.current"] += segment["active_size"]

                expected["requested_bytes.all.current"] += segment["requested_size"]
                expected[f"requested_bytes.{pool_str}.current"] += segment[
                    "requested_size"
                ]

                sum_requested = 0
                is_split = len(segment["blocks"]) > 1
                for block in segment["blocks"]:
                    if block["state"] == "active_allocated":
                        expected["allocation.all.current"] += 1
                        expected[f"allocation.{pool_str}.current"] += 1

                    if block["state"].startswith("active_"):
                        sum_requested += block["requested_size"]
                        expected["active.all.current"] += 1
                        expected[f"active.{pool_str}.current"] += 1

                    if block["state"] == "inactive" and is_split and not expandable:
                        expected["inactive_split.all.current"] += 1
                        expected[f"inactive_split.{pool_str}.current"] += 1
                        expected["inactive_split_bytes.all.current"] += block["size"]
                        expected[f"inactive_split_bytes.{pool_str}.current"] += block[
                            "size"
                        ]

                self.assertEqual(sum_requested, segment["requested_size"])

            for device, expected in expected_each_device.items():
                stats = torch.xpu.memory_stats(device)
                for k, v in expected.items():
                    self.assertEqual(v, stats[k])