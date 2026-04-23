def test_structured_metadata_matches_chrome_trace(self):
        # Compare metadata fields between events() and Chrome trace JSON to make sure they stay in parity
        # 1. Run a dummy workload with profiling enabled and collect the json/events() outputs
        # 2. Parse each event instance in the json and events() to create a key->value mapping
        #      - The key is a tuple of metadata fields that should be unique for each event
        #      - The value is a dict of metadata fields for that event
        # 3. Ensure that the keys and values match between the json and events() outputs

        from torch.autograd.profiler_util import _EVENT_METADATA_KEYS

        target_cats = ("cuda_runtime", "gpu_memcpy", "kernel")
        allowed_non_structured_trace_keys = {
            "External id",
            "correlation",
            "cbid",
            "cid",
            "device",
            "kind",
            "kernel",
            "ptr",
            "src",
            "dst",
        }
        supported_trace_keys = set(_EVENT_METADATA_KEYS).union(
            allowed_non_structured_trace_keys
        )

        def metadata_dict_from_trace_args(args):
            out = {}
            for kineto_key, (field_name, convert) in _EVENT_METADATA_KEYS.items():
                if kineto_key in args:
                    raw_value = args[kineto_key]
                    out[field_name] = (
                        convert(raw_value) if isinstance(raw_value, str) else raw_value
                    )
            return out

        def metadata_dict_from_function_event(fe):
            if fe.event_metadata is None:
                return {}

            out = {}
            for field_name, _ in _EVENT_METADATA_KEYS.values():
                val = getattr(fe.event_metadata, field_name)
                if val is not None:
                    out[field_name] = val
            return out

        with profile(
            activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
            experimental_config=torch._C._profiler._ExperimentalConfig(
                expose_kineto_event_metadata=True
            ),
        ) as prof:
            x = torch.randn(10, 10, device="cuda")
            y = torch.mm(x, x)
            z = x + y
            z.cpu()

        # Build a mapping from key to events() FunctionEvent metadata
        event_records = {}
        for fe in prof.events():
            if fe.external_id == 0 or fe.id == 0 or fe.activity_type not in target_cats:
                continue
            # Using just one of these keys could result in collisions, so try to uniquely identify the event with all of them
            key = (fe.name, fe.activity_type, fe.external_id, fe.id)
            self.assertNotIn(
                key,
                event_records,
                f"Duplicate FunctionEvent record key encountered: {key}",
            )
            event_records[key] = metadata_dict_from_function_event(fe)

        with TemporaryFileName(mode="w+") as fname:
            prof.export_chrome_trace(fname)
            with open(fname) as f:
                trace = json.load(f)

        json_records = {}
        # Track unexpected (event_name, cat, key) combos, deduplicated
        unexpected_combos: set[tuple[str, str, str]] = set()

        # Loop through the trace events to perform a comparison
        for te in trace["traceEvents"]:
            cat = te.get("cat", "")
            args = te.get("args", {})
            ext_id = args.get("External id")
            correlation = args.get("correlation")

            if ext_id is None or correlation is None:
                continue
            if cat not in target_cats:
                continue

            # Any metadata keys that show up in JSON should show up in events()
            for k in set(args) - supported_trace_keys:
                unexpected_combos.add((te["name"][:100], cat, k))

            # Build the same key from JSON to try to match with a FunctionEvent
            key = (te["name"], te["cat"], ext_id, correlation)
            self.assertNotIn(
                key,
                json_records,
                f"Duplicate Chrome trace record key encountered: {key}",
            )
            json_records[key] = metadata_dict_from_trace_args(args)

        failure_msg = """\
====================================================================================
IMPORTANT: Are you making a Kineto change or bumping the third_party/kineto
submodule hash and seeing this message?

New metadata keys (see below) were found in the Chrome trace JSON that are not
yet exposed through the profiler's events() API (i.e. EventMetadata in
torch/autograd/profiler_util.py).

To fix this properly, you need to make sure the new Kineto data makes its way
to the events() property. The steps are:

1. Add the new key(s) to _EVENT_METADATA_KEYS in torch/autograd/profiler_util.py
   with the appropriate field name and type converter.
2. Add corresponding field(s) to the EventMetadata dataclass in the same file.
3. If the key should NOT be mapped (e.g. it duplicates an existing FunctionEvent
   attribute), add it to allowed_non_structured_trace_keys in this test instead.

For a model PR to follow, see: https://github.com/pytorch/pytorch/pull/180100
===================================================================================="""
        if unexpected_combos:
            summary = "\n".join(
                f"  {name} ({cat}): {key!r}"
                for name, cat, key in sorted(unexpected_combos)
            )
            raise AssertionError(f"\n{failure_msg}\n\nUnmapped keys:\n{summary}")

        self.assertGreater(len(json_records), 0, "No device-side records were compared")
        self.assertEqual(
            set(event_records),
            set(json_records),
            "Device event identities differ between events() and Chrome trace JSON",
        )

        for key in json_records:
            expected_meta = json_records[key]
            actual_meta = event_records[key]
            self.assertEqual(
                actual_meta,
                expected_meta,
                f"{key}: structured metadata differs between events() and Chrome trace JSON",
            )