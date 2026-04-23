def _parse_kineto_results(
        self, result: _ProfilerResult, timeout_s: float | None = None
    ):
        # result.events() has most of the events - PyTorch op-level and device-level events

        timeout_ns = int(timeout_s * 1e9) if timeout_s is not None else None
        result_events = result.events()
        if timeout_ns is not None and timeout_ns < 0:
            raise ValueError("timeout_s must be non-negative")
        start_time_ns = perf_counter_ns()
        timed_out = False

        def _check_timeout() -> bool:
            """Check if timeout has been exceeded. Returns True if timed out."""
            nonlocal timed_out
            if timeout_ns is not None and not timed_out:
                elapsed_ns = perf_counter_ns() - start_time_ns
                if elapsed_ns >= timeout_ns:
                    timed_out = True
            return timed_out

        trace_start_ns = result.trace_start_ns()
        mem_records = [
            [evt, False] for evt in result_events if evt.name() == MEMORY_EVENT_NAME
        ]
        oom_records = [
            evt for evt in result_events if evt.name() == OUT_OF_MEMORY_EVENT_NAME
        ]
        mem_records_acc = MemRecordsAcc(mem_records)

        def _cpu_memory_usage(mem_record):
            return (
                mem_record.nbytes()
                if mem_record.device_type()
                in [DeviceType.CPU, DeviceType.MKLDNN, DeviceType.IDEEP]
                else 0
            )

        def _device_memory_usage(mem_record):
            return (
                mem_record.nbytes()
                if mem_record.device_type()
                in [
                    DeviceType.CUDA,
                    DeviceType.PrivateUse1,
                    DeviceType.HIP,
                    DeviceType.XPU,
                ]
                else 0
            )

        # Create and return FunctionEvent list, which contains all function events
        # Here 2 function events are created:
        # all_function_events contains all events associated with each kineto event from result
        all_function_events = []
        # frontend_function_events contains the events in aten or torch frontend level,
        # whose correlation id is 0
        frontend_function_events = []
        device_corr_map: dict[int, list[FunctionEvent]] = {}
        max_evt_id = 0
        for kineto_event in result_events:
            if _check_timeout():
                break

            if (
                _filter_name(kineto_event.name())
                or getattr(kineto_event, "is_hidden_event", lambda: False)()
            ):
                continue
            rel_start_ns = kineto_event.start_ns() - trace_start_ns
            rel_end_ns = kineto_event.end_ns() - trace_start_ns

            cpu_memory_usage = 0
            device_memory_usage = 0
            if kineto_event.device_type() == DeviceType.CPU:
                # find the corresponding memory allocation events
                for mem_record in mem_records_acc.in_interval(
                    kineto_event.start_ns(), kineto_event.end_ns()
                ):
                    cpu_memory_usage += _cpu_memory_usage(mem_record[0])
                    device_memory_usage += _device_memory_usage(mem_record[0])
                    mem_record[1] = True

            is_async = kineto_event.is_async() or (
                kineto_event.start_thread_id() != kineto_event.end_thread_id()
            )

            fe = FunctionEvent(
                id=kineto_event.correlation_id(),
                name=_rewrite_name(name=kineto_event.name(), with_wildcard=True),
                overload_name=kineto_event.overload_name(),
                trace_name=_rewrite_name(name=kineto_event.name(), with_wildcard=False),
                thread=kineto_event.start_thread_id(),
                start_us=rel_start_ns / 1000,
                end_us=rel_end_ns / 1000,
                fwd_thread=kineto_event.fwd_thread_id(),
                input_shapes=kineto_event.shapes(),
                concrete_inputs=kineto_event.concrete_inputs(),
                kwinputs=kineto_event.kwinputs(),
                stack=[
                    entry
                    for entry in kineto_event.stack()
                    if _filter_stack_entry(entry)
                ],
                scope=kineto_event.scope(),
                use_device=self.use_device,
                cpu_memory_usage=cpu_memory_usage,
                device_memory_usage=device_memory_usage,
                is_async=is_async,
                sequence_nr=kineto_event.sequence_nr(),
                device_type=kineto_event.device_type(),
                device_index=kineto_event.device_index(),
                device_resource_id=kineto_event.device_resource_id(),
                flops=kineto_event.flops(),
                is_user_annotation=kineto_event.is_user_annotation(),
                is_python_function=kineto_event.is_python_function(),
                activity_type=kineto_event.activity_type(),
                metadata_json=kineto_event.metadata_json(),
                extra_meta=kineto_event.extra_meta() or None,
                flow_id=kineto_event.flow_id(),
                flow_type=kineto_event.flow_type(),
                flow_start=kineto_event.flow_start(),
                external_id=kineto_event.external_id(),
                linked_correlation_id=kineto_event.linked_correlation_id(),
                structured_input_shapes=kineto_event.structured_input_shapes(),
                structured_input_strides=kineto_event.structured_input_strides(),
                input_dtypes=kineto_event.dtypes(),
                python_id=kineto_event.python_id(),
                python_parent_id=kineto_event.python_parent_id(),
                python_module_id=kineto_event.python_module_id(),
            )
            max_evt_id = max(max_evt_id, fe.id)
            if fe.device_type == DeviceType.CPU and not fe.is_async:
                if self.use_device == _get_privateuse1_backend_name():
                    privateuse1_time = kineto_event.privateuse1_elapsed_us()
                    if privateuse1_time > 0:
                        fe.append_kernel(fe.name, fe.device_index, privateuse1_time)
                        fe.is_legacy = True
                elif self.use_device == "cuda":
                    # Check if we have CUDA time as a fallback
                    cuda_time = kineto_event.cuda_elapsed_us()
                    if cuda_time > 0:
                        fe.append_kernel(fe.name, fe.device_index, cuda_time)
                        fe.is_legacy = True
            all_function_events.append(fe)
            corr_id = kineto_event.linked_correlation_id()
            if corr_id > 0:
                if corr_id not in device_corr_map:
                    device_corr_map[corr_id] = []
                device_corr_map[corr_id].append(fe)
            elif corr_id == 0:
                frontend_function_events.append(fe)
            else:
                raise RuntimeError(
                    f"Got negative correlation id {corr_id} in profiler post processing"
                )

        # associate device kernels and device runtime (CPU) with CPU events
        for fe in frontend_function_events:
            if (
                fe.device_type == DeviceType.CPU
                and not fe.is_async
                and fe.id in device_corr_map
            ):
                for f_evt in device_corr_map[fe.id]:
                    if f_evt.device_type in [
                        DeviceType.CUDA,
                        DeviceType.PrivateUse1,
                        DeviceType.XPU,
                    ]:
                        fe.append_kernel(
                            f_evt.name,
                            f_evt.device_index,
                            f_evt.time_range.end - f_evt.time_range.start,
                        )
                    elif f_evt.device_type == DeviceType.CPU:
                        # make sure that 'thread' of a CPU Kineto (e.g. Device Runtime) event is associated
                        # with the 'thread' of the corresponding linked PyTorch event to properly track
                        # parents and children
                        f_evt.thread = fe.thread

        def _create_function_event_for_memory_events(evt):
            rel_start_ns = evt.start_ns() - trace_start_ns
            fe = FunctionEvent(
                id=max_evt_id,
                name=evt.name(),
                overload_name="",
                trace_name=None,  # not outputting in the trace
                thread=evt.start_thread_id(),
                start_us=rel_start_ns / 1000,
                end_us=rel_start_ns / 1000,  # no duration
                fwd_thread=evt.start_thread_id(),
                input_shapes=[],
                stack=[],
                scope=0,  # RecordScope::FUNCTION
                use_device=self.use_device,
                cpu_memory_usage=_cpu_memory_usage(evt),
                device_memory_usage=_device_memory_usage(evt),
                is_async=False,
                sequence_nr=-1,
                device_type=DeviceType.CPU,
                device_index=0,
            )
            return fe

        # output top-level memory events
        for mem_record in mem_records:
            if _check_timeout():
                break

            if not mem_record[1]:
                max_evt_id += 1
                fe = _create_function_event_for_memory_events(mem_record[0])
                all_function_events.append(fe)

        for oom_record in oom_records:
            if _check_timeout():
                break

            max_evt_id += 1
            fe = _create_function_event_for_memory_events(oom_record)
            all_function_events.append(fe)

        if timed_out:
            log.warning(
                "Profiler _parse_kineto_results timed out after %.3f seconds, "
                "returning partial results with %d events",
                timeout_s,
                len(all_function_events),
            )

        all_function_events.sort(
            key=lambda evt: [evt.time_range.start, -evt.time_range.end]
        )
        return all_function_events