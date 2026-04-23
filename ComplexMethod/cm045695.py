def run_with_event_loop(event_loop: asyncio.AbstractEventLoop):
                with (
                    monitor_stats(
                        monitoring_level,
                        node_names,
                        default_logging=self.default_logging,
                        process_id=pathway_config.process_id,
                    ) as stats_monitor,
                    otel.with_logging_handler(),
                    get_persistence_engine_config(
                        self.persistence_config
                    ) as persistence_engine_config,
                ):
                    try:
                        return api.run_with_new_graph(
                            logic,
                            event_loop=event_loop,
                            ignore_asserts=self.ignore_asserts,
                            stats_monitor=stats_monitor,
                            monitoring_level=monitoring_level,
                            with_http_server=self.with_http_server,
                            persistence_config=persistence_engine_config,
                            telemetry_config=otel.engine_telemetry_config(trace_parent),
                            license_key=self.license_key,
                            terminate_on_error=self.terminate_on_error,
                            max_expression_batch_size=self.max_expression_batch_size,
                        )
                    except api.EngineErrorWithTrace as e:
                        error, frame = e.args
                        if frame is not None:
                            trace.add_pathway_trace_note(
                                error,
                                trace.Frame(
                                    filename=frame.file_name,
                                    line_number=frame.line_number,
                                    line=frame.line,
                                    function=frame.function,
                                ),
                            )
                        raise error from None
                    except api.OtherWorkerError:
                        if pathway_config.suppress_other_worker_errors:
                            sys.exit(1)
                        else:
                            raise
                    finally:
                        for node in graph.G._current_scope.nodes:
                            if (
                                isinstance(node, OutputOperator)
                                and isinstance(node.datasink, datasink.GenericDataSink)
                                and node.datasink.on_pipeline_finished is not None
                            ):
                                node.datasink.on_pipeline_finished()