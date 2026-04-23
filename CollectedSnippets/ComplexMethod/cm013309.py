def test_rpc_profiling_remote_record_function(self):
        # test that functions run over RPC with record_function show the expected
        # profiled block.
        if self.rank != 1:
            return
        dst_ranks = [i for i in range(self.world_size) if i != self.rank]
        for dst_rank in dst_ranks:
            dst_worker = worker_name(dst_rank)
            with _profile() as prof:
                fut = rpc.rpc_async(dst_worker, udf_with_torch_ops, args=(-1, True))
                fut.wait()

            function_events = prof.function_events
            record_function_remote_event = [
                evt for evt in function_events if "##forward##" in evt.name
            ]
            self.assertEqual(1, len(record_function_remote_event))
            record_function_remote_event = record_function_remote_event[0]
            self.assertEqual(record_function_remote_event.node_id, dst_rank)
            # cpu_children only returns direct children, so here we get all
            # children recursively.

            def get_cpu_children(event):
                if not event.cpu_children:
                    return []
                cpu_children = event.cpu_children
                for e in event.cpu_children:
                    cpu_children.extend(get_cpu_children(e))
                return cpu_children

            remote_children = get_cpu_children(record_function_remote_event)
            # Get local children and verify parity.
            with _profile() as prof:
                udf_with_torch_ops(-1, True)

            local_function_events = prof.function_events
            local_record_function_event = next(
                evt for evt in local_function_events if "##forward##" in evt.name
            )
            local_children = get_cpu_children(local_record_function_event)
            local_children_names = [evt.name for evt in local_children]

            REMOTE_OP_STR = "#remote_op: "

            def convert_remote_to_local(event_name):
                remote_op_key = REMOTE_OP_STR
                return event_name[event_name.find(remote_op_key) + len(remote_op_key) :]

            for evt in remote_children:
                local_name = convert_remote_to_local(evt.name)
                self.assertTrue(local_name in local_children_names)