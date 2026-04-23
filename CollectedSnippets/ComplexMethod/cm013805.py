def timeline(self) -> tuple[tuple[int, Action, KeyAndID, int], ...]:
        output: list[tuple[int, Action, KeyAndID, int]] = []
        allocation_times: dict[tuple[TensorKey, bool], int] = {}
        live_unknown: dict[tuple[int, torch.device], Literal[True]] = {}

        for event in self._op_tree.dfs():
            if event.typed[0] == _EventType.Allocation:
                alloc_fields = event.typed[1]
                alloc_size = alloc_fields.alloc_size
                is_allocation = alloc_size > 0
                t = event.start_time_ns

                tkey = TensorKey.from_allocation(alloc_fields)
                if tkey is not None:
                    allocation_times[(tkey, is_allocation)] = t

                else:
                    key = Key(alloc_fields.device)
                    ptr_and_device = (alloc_fields.ptr, key.device)
                    if is_allocation:
                        if ptr_and_device in live_unknown:
                            output.append(
                                (t, Action.INCREMENT_VERSION, (key, 0), alloc_size)
                            )
                        else:
                            live_unknown[ptr_and_device] = True
                            output.append((t, Action.CREATE, (key, 0), alloc_size))
                    else:
                        output.append((t, Action.DESTROY, (key, 0), -alloc_size))
                        if not live_unknown.pop(ptr_and_device, False):
                            output.append(
                                (-1, Action.PREEXISTING, (key, 0), -alloc_size)
                            )

        snapshot = self._category_snapshot()
        last_version = dict(sorted(snapshot.keys()))

        events: list[tuple[int, Action, TensorAndID]] = [
            (-1, Action.PREEXISTING, (key, version))
            for key, version in snapshot
            if (key, True) not in allocation_times and version == 0
        ]

        for node in self._data_flow_graph.flow_nodes:
            for key, edge in node._edges.items():
                if edge.is_allocation:
                    t = allocation_times[(key, True)]
                    events.append((t, Action.CREATE, (key, 0)))

                elif edge.mutated:
                    t = node._event.start_time_ns
                    version = edge.input_version
                    if version is None:
                        raise AssertionError(f"input_version is None for key {key}")
                    events.append((t, Action.INCREMENT_VERSION, (key, version)))

                if edge.is_deletion:
                    t = allocation_times[(key, False)]
                    events.append((t, Action.DESTROY, (key, last_version[key])))

        output.extend(
            (time, action, (key, version), self._size_map[key])
            for time, action, (key, version) in events
        )

        output.sort(key=lambda x: (x[0], x[1].value))
        return tuple(output)