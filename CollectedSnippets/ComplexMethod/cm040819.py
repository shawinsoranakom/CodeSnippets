def list_executions(
        self,
        context: RequestContext,
        state_machine_arn: Arn = None,
        status_filter: ExecutionStatus = None,
        max_results: PageSize = None,
        next_token: ListExecutionsPageToken = None,
        map_run_arn: LongArn = None,
        redrive_filter: ExecutionRedriveFilter = None,
        **kwargs,
    ) -> ListExecutionsOutput:
        self._validate_state_machine_arn(state_machine_arn)
        assert_pagination_parameters_valid(
            max_results=max_results,
            next_token=next_token,
            next_token_length_limit=3096,
        )
        max_results = normalise_max_results(max_results)

        state_machine = self.get_store(context).state_machines.get(state_machine_arn)
        if state_machine is None:
            self._raise_state_machine_does_not_exist(state_machine_arn)

        if state_machine.sm_type != StateMachineType.STANDARD:
            self._raise_state_machine_type_not_supported()

        # TODO: add support for paging

        allowed_execution_status = [
            ExecutionStatus.SUCCEEDED,
            ExecutionStatus.TIMED_OUT,
            ExecutionStatus.PENDING_REDRIVE,
            ExecutionStatus.ABORTED,
            ExecutionStatus.FAILED,
            ExecutionStatus.RUNNING,
        ]

        validation_errors = []

        if status_filter and status_filter not in allowed_execution_status:
            validation_errors.append(
                f"Value '{status_filter}' at 'statusFilter' failed to satisfy constraint: Member must satisfy enum value set: [{', '.join(allowed_execution_status)}]"
            )

        if not state_machine_arn and not map_run_arn:
            validation_errors.append("Must provide a StateMachine ARN or MapRun ARN")

        if validation_errors:
            errors_message = "; ".join(validation_errors)
            message = f"{len(validation_errors)} validation {'errors' if len(validation_errors) > 1 else 'error'} detected: {errors_message}"
            raise CommonServiceException(message=message, code="ValidationException")

        executions: ExecutionList = [
            execution.to_execution_list_item()
            for execution in self.get_store(context).executions.values()
            if self._list_execution_filter(
                execution,
                state_machine_arn=state_machine_arn,
                status_filter=status_filter,
            )
        ]

        executions.sort(key=lambda item: item["startDate"], reverse=True)

        paginated_executions = PaginatedList(executions)
        page, token_for_next_page = paginated_executions.get_page(
            token_generator=lambda item: get_next_page_token_from_arn(item.get("executionArn")),
            page_size=max_results,
            next_token=next_token,
        )

        return ListExecutionsOutput(executions=page, nextToken=token_for_next_page)