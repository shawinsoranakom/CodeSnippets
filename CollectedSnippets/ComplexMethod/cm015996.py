def test_profiler_overload_names(self):
        from torch.library import _scoped_library, fallthrough_kernel

        def validate_json(prof):
            print()
            with TemporaryFileName(mode="w+") as fname:
                prof.export_chrome_trace(fname)
                with open(fname) as f:
                    events = json.load(f)["traceEvents"]
                    self.assertTrue(
                        any("aten::add.Tensor" in e["name"] for e in events)
                    )
                    self.assertTrue(any("aten::add.out" in e["name"] for e in events))

        with _scoped_library("aten", "IMPL") as my_lib:
            my_lib.impl("add.Tensor", fallthrough_kernel, "CPU")
            experimental_config = torch._C._profiler._ExperimentalConfig(
                capture_overload_names=True
            )
            with profile(
                experimental_config=experimental_config,
                activities=[ProfilerActivity.CPU],
            ) as prof:
                torch.add(1, 5)

            # The following execution trace is expected
            #
            # Dispatch trace:
            # [call] op=[aten::add.Tensor], key=[AutogradCPU]
            #   [redispatch] op=[aten::add.Tensor], key=[Undefined]
            #     [call] op=[aten::empty.memory_format], key=[BackendSelect]
            #       [redispatch] op=[aten::empty.memory_format], key=[CPU]
            #     [call] op=[aten::add.out], key=[CPU]
            #
            # prof.table()
            # ---------------  ---------------  ------------  ------------  ------------  ------------  ------------  ------------
            #            Name    Overload Name    Self CPU %      Self CPU   CPU total %     CPU total  CPU time avg    # of Calls
            # ---------------  ---------------  ------------  ------------  ------------  ------------  ------------  ------------
            #       aten::add           Tensor        71.97%     130.887us       100.00%     181.873us     181.873us             1
            #     aten::empty    memory_format         8.52%      15.489us         8.52%      15.489us      15.489us             1
            #       aten::add              out        19.52%      35.497us        19.52%      35.497us      35.497us             1
            # ---------------  ---------------  ------------  ------------  ------------  ------------  ------------  ------------

            # aten::add.out and aten::empty.memory_format are children of aten::add.Tensor
            aten_add_parent: list[FunctionEvent] = [
                event for event in prof.events() if len(event.cpu_children) == 2
            ]
            if len(aten_add_parent) != 1:
                raise AssertionError(
                    f"Expected 1 parent event, got {len(aten_add_parent)}"
                )
            aten_add_parent = aten_add_parent[0]
            if aten_add_parent.overload_name != "Tensor":
                raise AssertionError(
                    f"Expected overload_name 'Tensor', got '{aten_add_parent.overload_name}'"
                )

            aten_add_out_event = [
                c for c in aten_add_parent.cpu_children if c.overload_name == "out"
            ]
            if len(aten_add_out_event) != 1:
                raise AssertionError(
                    f"Expected 1 out event, got {len(aten_add_out_event)}"
                )

            # Without group_by_overload_name, the overload name is ignored in the key averages
            key_averages = prof.key_averages()
            if len(key_averages) != 2:
                raise AssertionError(
                    f"Expected 2 key averages, got {len(key_averages)}"
                )
            if "Overload Name" in key_averages.table():
                raise AssertionError("Overload Name should not be in table")

            key_averages = prof.key_averages(group_by_overload_name=True)
            if len(key_averages) != 3:
                raise AssertionError(
                    f"Expected 3 key averages with group_by_overload_name, got {len(key_averages)}"
                )
            if "Overload Name" not in key_averages.table():
                raise AssertionError("Overload Name should be in table")
            validate_json(prof)