def deploy_loop(
        self,
        resource_provider: ResourceProvider,
        resource: dict,
        raw_payload: ResourceProviderPayload,
        max_timeout: int = config.CFN_PER_RESOURCE_TIMEOUT,
        sleep_time: float = 1,
    ) -> ProgressEvent[Properties]:
        payload = copy.deepcopy(raw_payload)

        max_iterations = max(ceil(max_timeout / sleep_time), 10)

        for current_iteration in range(max_iterations):
            resource_type = get_resource_type({"Type": raw_payload["resourceType"]})
            resource["SpecifiedProperties"] = raw_payload["requestData"]["resourceProperties"]

            try:
                event = self.execute_action(resource_provider, payload)
            except ClientError:
                LOG.error(
                    "client error invoking '%s' handler for resource '%s' (type '%s')",
                    raw_payload["action"],
                    raw_payload["requestData"]["logicalResourceId"],
                    resource_type,
                )
                raise

            match event.status:
                case OperationStatus.FAILED:
                    return event
                case OperationStatus.SUCCESS:
                    if not hasattr(resource_provider, "SCHEMA"):
                        raise Exception(
                            "A ResourceProvider should always have a SCHEMA property defined."
                        )
                    resource_type_schema = resource_provider.SCHEMA
                    if raw_payload["action"] != "Remove":
                        physical_resource_id = (
                            self.extract_physical_resource_id_from_model_with_schema(
                                event.resource_model,
                                raw_payload["resourceType"],
                                resource_type_schema,
                            )
                        )

                        resource["PhysicalResourceId"] = physical_resource_id
                        resource["Properties"] = event.resource_model
                        resource["_last_deployed_state"] = copy.deepcopy(event.resource_model)
                    return event
                case OperationStatus.IN_PROGRESS:
                    # update the shared state
                    context = {**payload["callbackContext"], **event.custom_context}
                    payload["callbackContext"] = context
                    payload["requestData"]["resourceProperties"] = event.resource_model
                    resource["Properties"] = event.resource_model

                    if current_iteration < config.CFN_NO_WAIT_ITERATIONS:
                        pass
                    else:
                        time.sleep(sleep_time)

                case OperationStatus.PENDING:
                    # come back to this resource in another iteration
                    return event
                case invalid_status:
                    raise ValueError(
                        f"Invalid OperationStatus ({invalid_status}) returned for resource {raw_payload['requestData']['logicalResourceId']} (type {raw_payload['resourceType']})"
                    )

        else:
            raise TimeoutError(
                f"Resource deployment for resource {raw_payload['requestData']['logicalResourceId']} (type {raw_payload['resourceType']}) timed out."
            )