def update_event_source_mapping_v2(
        self,
        context: RequestContext,
        request: UpdateEventSourceMappingRequest,
    ) -> EventSourceMappingConfiguration:
        # TODO: test and implement this properly (quite complex with many validations and limitations!)
        LOG.warning(
            "Updating Lambda Event Source Mapping is in experimental state and not yet fully tested."
        )
        state = lambda_stores[context.account_id][context.region]
        request_data = {**request}
        uuid = request_data.pop("UUID", None)
        if not uuid:
            raise ResourceNotFoundException(
                "The resource you requested does not exist.", Type="User"
            )
        old_event_source_mapping = state.event_source_mappings.get(uuid)
        esm_worker = self.esm_workers.get(uuid)
        if old_event_source_mapping is None or esm_worker is None:
            raise ResourceNotFoundException(
                "The resource you requested does not exist.", Type="User"
            )  # TODO: test?

        # normalize values to overwrite
        event_source_mapping = old_event_source_mapping | request_data

        temp_params = {}  # values only set for the returned response, not saved internally (e.g. transient state)

        # Validate the newly updated ESM object. We ignore the output here since we only care whether an Exception is raised.
        function_arn, _, _, function_version, function_role = self.validate_event_source_mapping(
            context, event_source_mapping
        )

        # remove the FunctionName field
        event_source_mapping.pop("FunctionName", None)

        if function_arn:
            event_source_mapping["FunctionArn"] = function_arn

        # Only apply update if the desired state differs
        enabled = request.get("Enabled")
        if enabled is not None:
            if enabled and old_event_source_mapping["State"] != EsmState.ENABLED:
                event_source_mapping["State"] = EsmState.ENABLING
            # TODO: What happens when trying to update during an update or failed state?!
            elif not enabled and old_event_source_mapping["State"] == EsmState.ENABLED:
                event_source_mapping["State"] = EsmState.DISABLING
        else:
            event_source_mapping["State"] = EsmState.UPDATING

        # To ensure parity, certain responses need to be immediately returned
        temp_params["State"] = event_source_mapping["State"]

        state.event_source_mappings[uuid] = event_source_mapping

        # TODO: Currently, we re-create the entire ESM worker. Look into approach with better performance.
        worker_factory = EsmWorkerFactory(
            event_source_mapping, function_role, request.get("Enabled", esm_worker.enabled)
        )

        # Get a new ESM worker object but do not active it, since the factory holds all logic for creating new worker from configuration.
        updated_esm_worker = worker_factory.get_esm_worker()
        self.esm_workers[uuid] = updated_esm_worker

        # We should stop() the worker since the delete() will remove the ESM from the state mapping.
        esm_worker.stop()
        # This will either create an EsmWorker in the CREATING state if enabled. Otherwise, the DISABLING state is set.
        updated_esm_worker.create()

        return {**event_source_mapping, **temp_params}