def _eval_execution(self, env: Environment) -> None:
        self.max_concurrency_decl.eval(env=env)
        max_concurrency_num = env.stack.pop()
        label = self.label.label if self.label else None

        # Despite MaxConcurrency and Tolerance fields being state level fields, AWS StepFunctions evaluates only
        # MaxConcurrency as a state level field. In contrast, Tolerance is evaluated only after the state start
        # event but is logged with event IDs coherent with state level fields. To adhere to this quirk, an evaluation
        # frame from this point is created for the evaluation of Tolerance fields following the state start event.
        frame: Environment = env.open_frame()
        frame.states.reset(input_value=env.states.get_input())
        frame.stack = copy.deepcopy(env.stack)

        try:
            # ItemsPath in DistributedMap states is only used if a JSONinput is passed from the previous state.
            if (
                not isinstance(self.iteration_component, DistributedIterationComponent)
                or self.item_reader is None
            ):
                if self.items_path:
                    self.items_path.eval(env=env)

            if self.items:
                self.items.eval(env=env)

            if self.item_reader:
                env.event_manager.add_event(
                    context=env.event_history_context,
                    event_type=HistoryEventType.MapStateStarted,
                    event_details=EventDetails(
                        mapStateStartedEventDetails=MapStateStartedEventDetails(length=0)
                    ),
                )
                input_items = None
            else:
                input_items = env.stack.pop()
                # TODO: This should probably be raised within an Items EvalComponent
                if not isinstance(input_items, list):
                    error_name = StatesErrorName(typ=StatesErrorNameType.StatesQueryEvaluationError)
                    failure_event = FailureEvent(
                        env=env,
                        error_name=error_name,
                        event_type=HistoryEventType.EvaluationFailed,
                        event_details=EventDetails(
                            evaluationFailedEventDetails=EvaluationFailedEventDetails(
                                cause=f"Map state input must be an array but was: {type(input_items)}",
                                error=error_name.error_name,
                            )
                        ),
                    )
                    raise FailureEventException(failure_event=failure_event)
                env.event_manager.add_event(
                    context=env.event_history_context,
                    event_type=HistoryEventType.MapStateStarted,
                    event_details=EventDetails(
                        mapStateStartedEventDetails=MapStateStartedEventDetails(
                            length=len(input_items)
                        )
                    ),
                )

            self.tolerated_failure_count_decl.eval(env=frame)
            tolerated_failure_count = frame.stack.pop()
            self.tolerated_failure_percentage_decl.eval(env=frame)
            tolerated_failure_percentage = frame.stack.pop()
        finally:
            env.close_frame(frame)

        if isinstance(self.iteration_component, InlineIterator):
            eval_input = InlineIteratorEvalInput(
                state_name=self.name,
                max_concurrency=max_concurrency_num,
                input_items=input_items,
                parameters=self.parameters,
                item_selector=self.item_selector,
            )
        elif isinstance(self.iteration_component, InlineItemProcessor):
            eval_input = InlineItemProcessorEvalInput(
                state_name=self.name,
                max_concurrency=max_concurrency_num,
                input_items=input_items,
                item_selector=self.item_selector,
                parameters=self.parameters,
            )
        else:
            map_run_record = MapRunRecord(
                state_machine_arn=env.states.context_object.context_object_data["StateMachine"][
                    "Id"
                ],
                execution_arn=env.states.context_object.context_object_data["Execution"]["Id"],
                max_concurrency=max_concurrency_num,
                tolerated_failure_count=tolerated_failure_count,
                tolerated_failure_percentage=tolerated_failure_percentage,
                label=label,
            )
            env.map_run_record_pool_manager.add(map_run_record)
            # Choose the distributed input type depending on whether the definition
            # asks for the legacy Iterator component or an ItemProcessor
            if isinstance(self.iteration_component, DistributedIterator):
                distributed_eval_input_class = DistributedIteratorEvalInput
            elif isinstance(self.iteration_component, DistributedItemProcessor):
                distributed_eval_input_class = DistributedItemProcessorEvalInput
            else:
                raise RuntimeError(
                    f"Unknown iteration component of type '{type(self.iteration_component)}' '{self.iteration_component}'."
                )
            eval_input = distributed_eval_input_class(
                state_name=self.name,
                max_concurrency=max_concurrency_num,
                input_items=input_items,
                parameters=self.parameters,
                item_selector=self.item_selector,
                item_reader=self.item_reader,
                tolerated_failure_count=tolerated_failure_count,
                tolerated_failure_percentage=tolerated_failure_percentage,
                label=label,
                map_run_record=map_run_record,
            )

        env.stack.append(eval_input)
        self.iteration_component.eval(env)

        if self.result_writer:
            self.result_writer.eval(env)

        env.event_manager.add_event(
            context=env.event_history_context,
            event_type=HistoryEventType.MapStateSucceeded,
            update_source_event_id=False,
        )