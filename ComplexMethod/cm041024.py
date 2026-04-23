def execute_action(
        self, resource_provider: ResourceProvider, raw_payload: ResourceProviderPayload
    ) -> ProgressEvent[Properties]:
        change_type = raw_payload["action"]
        request = convert_payload(
            stack_name=self.stack_name, stack_id=self.stack_id, payload=raw_payload
        )

        match change_type:
            case "Add":
                return resource_provider.create(request)
            case "Dynamic" | "Modify":
                try:
                    return resource_provider.update(request)
                except NotImplementedError:
                    feature_request_url = "https://github.com/localstack/localstack/issues/new?template=feature-request.yml"
                    LOG.warning(
                        'Unable to update resource type "%s", id "%s", '
                        "the update operation is not implemented for this resource. "
                        "Please consider submitting a feature request at this URL: %s",
                        request.resource_type,
                        request.logical_resource_id,
                        feature_request_url,
                    )
                    if request.previous_state is None:
                        # this is an issue with our update detection. We should never be in this state.
                        request.action = "Add"
                        return resource_provider.create(request)

                    return ProgressEvent(
                        status=OperationStatus.SUCCESS, resource_model=request.previous_state
                    )
                except Exception as e:
                    # FIXME: this fallback should be removed after fixing updates in general (order/dependenies)
                    # catch-all for any exception that looks like a not found exception
                    if check_not_found_exception(e, request.resource_type, request.desired_state):
                        return ProgressEvent(
                            status=OperationStatus.SUCCESS, resource_model=request.previous_state
                        )

                    return ProgressEvent(
                        status=OperationStatus.FAILED,
                        resource_model={},
                        message=f"Failed to delete resource with id {request.logical_resource_id} of type {request.resource_type}",
                        custom_context={"exception": e},
                    )
            case "Remove":
                try:
                    return resource_provider.delete(request)
                except Exception as e:
                    # catch-all for any exception that looks like a not found exception
                    if check_not_found_exception(e, request.resource_type, request.desired_state):
                        return ProgressEvent(status=OperationStatus.SUCCESS, resource_model={})

                    return ProgressEvent(
                        status=OperationStatus.FAILED,
                        resource_model={},
                        message=f"Failed to delete resource with id {request.logical_resource_id} of type {request.resource_type}",
                        custom_context={"exception": e},
                    )
            case _:
                raise NotImplementedError(change_type)