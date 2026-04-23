def create_resource_provider_payload(
        self,
        action: ChangeAction,
        logical_resource_id: str,
        resource_type: str,
        before_properties: PreprocProperties | None,
        after_properties: PreprocProperties | None,
    ) -> ResourceProviderPayload | None:
        # FIXME: use proper credentials
        creds: Credentials = {
            "accessKeyId": self._change_set.stack.account_id,
            "secretAccessKey": INTERNAL_AWS_SECRET_ACCESS_KEY,
            "sessionToken": "",
        }
        before_properties_value = before_properties.properties if before_properties else None
        after_properties_value = after_properties.properties if after_properties else None

        match action:
            case ChangeAction.Add:
                resource_properties = after_properties_value or {}
                previous_resource_properties = None
            case ChangeAction.Modify | ChangeAction.Dynamic:
                resource_properties = after_properties_value or {}
                previous_resource_properties = before_properties_value or {}
            case ChangeAction.Remove:
                resource_properties = before_properties_value or {}
                # previous_resource_properties = None
                # HACK: our providers use a mix of `desired_state` and `previous_state` so ensure the payload is present for both
                previous_resource_properties = resource_properties
            case _:
                raise NotImplementedError(f"Action '{action}' not handled")

        resource_provider_payload: ResourceProviderPayload = {
            "awsAccountId": self._change_set.stack.account_id,
            "callbackContext": {},
            "stackId": self._change_set.stack.stack_name,
            "resourceType": resource_type,
            "resourceTypeVersion": "000000",
            # TODO: not actually a UUID
            "bearerToken": str(uuid.uuid4()),
            "region": self._change_set.stack.region_name,
            "action": str(action),
            "requestData": {
                "logicalResourceId": logical_resource_id,
                "resourceProperties": resource_properties,
                "previousResourceProperties": previous_resource_properties,
                "callerCredentials": creds,
                "providerCredentials": creds,
                "systemTags": {},
                "previousSystemTags": {},
                "stackTags": {},
                "previousStackTags": {},
            },
        }
        return resource_provider_payload