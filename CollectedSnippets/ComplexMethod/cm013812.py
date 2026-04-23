def compute_queue_depth(self):
        """
        Computes queue_depth at each event. This will calculate the queue depth data for
        All the events in the tree.
        This will return a list of Interval of queue depth data of cuda launch and kernels.
        """
        if self.profile.kineto_results is None:
            raise AssertionError("kineto_results must not be None")
        cuda_event_list = self.profile.kineto_results.events()

        def is_cuda_launch_kernel(e):
            """Check if the event is a CUDA launch kernel."""
            launch_patterns = {
                "cudaLaunchKernel",  # Standard CUDA
                "cudaLaunchKernelExC",  # Extended C
                "__cudaLaunchKernel",  # Internal
                "cudaLaunchCooperativeKernel",  # Collaborative (single-device)
                "cudaLaunchCooperativeKernelMultiDevice",  # Collaborative (multi-devices)
            }
            name = str(getattr(e, "name", e))
            return any(name.startswith(pattern) for pattern in launch_patterns)

        def is_cuda_kernel(e):
            """Check if the event is a CUDA runtime kernel."""
            # Check if the kernel is CUDA
            if e.device_type() != DeviceType.CUDA:
                return False

            name = str(getattr(e, "name", e)).lower()

            # Exclude memory operations
            exclude_patterns = {"mem", "cpy", "alloc", "free"}

            return not any(pattern in name for pattern in exclude_patterns)

        cuda_launch_events = sorted(
            (e for e in cuda_event_list if is_cuda_launch_kernel(e)),
            key=lambda x: x.start_ns(),
        )
        cuda_kernel_events = sorted(
            (e for e in cuda_event_list if is_cuda_kernel(e)),
            key=lambda x: x.start_ns(),
        )

        self.cuda_events = sorted(
            cuda_launch_events + cuda_kernel_events, key=lambda x: x.start_ns()
        )

        kernel_mapping: dict[_KinetoEvent, int] = {}
        last_mapped_kernel = 0
        for cuda_launch_event in cuda_launch_events:
            index = index_of_first_match(
                cuda_kernel_events,
                lambda x: x.linked_correlation_id()
                == cuda_launch_event.linked_correlation_id(),
                start=last_mapped_kernel,
            )
            kernel_mapping[cuda_launch_event] = index
            last_mapped_kernel = index if index is not None else last_mapped_kernel

        current_kernel_index = 0
        spawned_kernel_index = -1

        all_events = cuda_launch_events + cuda_kernel_events + self.events

        def new_old_event_comparator(event):
            if hasattr(event, "start_us"):
                return event.start_us() * 1000
            if hasattr(event, "start_ns"):
                return event.start_ns()
            if hasattr(event, "start_time_ns"):
                return event.start_time_ns
            raise Exception("Unknown Event Type")  # noqa: TRY002

        queue_depth_list: list[Interval] = []
        all_events.sort(key=new_old_event_comparator)
        for event in all_events:
            # Find latest cuda kernel event
            if hasattr(event, "start_us"):
                start_time = event.start_us() * 1000
                # pyrefly: ignore [missing-attribute]
                end_time = (event.start_us() + event.duration_us()) * 1000
                # Find current spawned cuda kernel event
                if event in kernel_mapping and kernel_mapping[event] is not None:
                    spawned_kernel_index = kernel_mapping[event]
            if hasattr(event, "start_ns"):
                start_time = event.start_ns()
                end_time = event.start_ns() + event.duration_ns()
                # Find current spawned cuda kernel event
                if event in kernel_mapping and kernel_mapping[event] is not None:
                    spawned_kernel_index = kernel_mapping[event]
            elif hasattr(event, "start_time_ns"):
                start_time = event.start_time_ns  # type: ignore[attr-defined]
                end_time = event.end_time_ns  # type: ignore[attr-defined]

            while (
                current_kernel_index < len(cuda_kernel_events)
                and (cuda_kernel_events[current_kernel_index].start_ns()) <= start_time  # type: ignore[possibly-undefined]
            ):
                current_kernel_index += 1
            current_queue_depth = spawned_kernel_index - current_kernel_index + 1
            current_queue_depth = max(current_queue_depth, 0)

            if hasattr(event, "start_us") or hasattr(event, "start_ns"):
                queue_depth_list.append(
                    Interval(start_time, end_time, current_queue_depth)  # type: ignore[possibly-undefined]
                )
            elif hasattr(event, "start_time_ns"):
                self.metrics[EventKey(event)].queue_depth = current_queue_depth

        return queue_depth_list