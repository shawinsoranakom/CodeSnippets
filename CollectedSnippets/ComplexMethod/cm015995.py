def load_mock_profile():
        accept = expecttest.ACCEPT
        json_file_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "profiler_utils_mock_events.json",
        )
        if accept and torch.cuda.is_available():

            def garbage_code(x):
                for i in range(5):
                    x[0, i] = i

            x = torch.ones((4096, 4096), device="cuda")
            x = x @ x
            with profile(
                activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
                record_shapes=True,
                with_stack=True,
            ) as prof:
                for _ in range(5):
                    x = x @ x
                garbage_code(x)
                for _ in range(5):
                    x = x @ x

            kineto_events = [
                {
                    "_name": e.name,
                    "_start_ns": e.start_ns(),
                    "_duration_ns": e.duration_ns(),
                    "_linked_correlation_id": e.linked_correlation_id(),
                    "_device_type": 1 if e.device_type() == DeviceType.CUDA else 0,
                }
                for e in prof.profiler.kineto_results.events()
            ]

            def EventTreeDFS(event_tree):
                from collections import deque

                stack = deque(event_tree)
                while stack:
                    curr_event = stack.pop()
                    yield curr_event
                    for child_event in curr_event.children:
                        stack.append(child_event)

            profiler_events = [
                {
                    "_name": e.name,
                    "id": e.id,
                    "start_time_ns": e.start_time_ns,
                    "duration_time_ns": e.duration_time_ns,
                    "correlation_id": e.correlation_id,
                    "children": [child.id for child in e.children],
                    "parent": e.parent.id if e.parent else None,
                }
                for e in EventTreeDFS(
                    prof.profiler.kineto_results.experimental_event_tree()
                )
            ]

            with open(json_file_path, "w") as f:
                json.dump([kineto_events, profiler_events], f)

        if not os.path.exists(json_file_path):
            raise AssertionError(f"JSON file not found: {json_file_path}")
        with open(json_file_path) as f:
            kineto_events, profiler_events = json.load(f)

        cuda_events = [MockKinetoEvent(*event.values()) for event in kineto_events]
        cpu_events = []
        id_map = {}
        for e in profiler_events:
            event = MockProfilerEvent(**e)
            id_map[event.id] = event
            cpu_events.append(event)
        for event in cpu_events:
            parent = None if event.parent is None else id_map[event.parent]
            children = [id_map[child] for child in event.children]
            event.__post__init__(parent, children)
        cpu_events = [event for event in cpu_events if event.parent is None]
        profiler = unittest.mock.Mock()
        profiler.kineto_results = unittest.mock.Mock()
        profiler.kineto_results.events = unittest.mock.Mock(return_value=cuda_events)
        profiler.kineto_results.experimental_event_tree = unittest.mock.Mock(
            return_value=cpu_events
        )
        return profiler