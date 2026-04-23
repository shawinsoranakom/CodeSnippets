def validate_request(self) -> None:
        """
        :raises BadRequestParameters if the request has required parameters which are not present
        :raises BadRequestBody if the request has required body validation with a model and it does not respect it
        :return: None
        """
        # make all the positive checks first
        if self.context.resource is None or "resourceMethods" not in self.context.resource:
            return

        resource_methods = self.context.resource["resourceMethods"]
        if self.context.method not in resource_methods and "ANY" not in resource_methods:
            return

        # check if there is validator for the resource
        resource = resource_methods.get(self.context.method, resource_methods.get("ANY", {}))
        if not (resource.get("requestValidatorId") or "").strip():
            return

        # check if there is a validator for this request
        validator = self.rest_api_container.validators.get(resource["requestValidatorId"])
        if not validator:
            return

        if self.should_validate_request(validator) and (
            missing_parameters := self._get_missing_required_parameters(resource)
        ):
            message = f"Missing required request parameters: [{', '.join(missing_parameters)}]"
            raise BadRequestParameters(message=message)

        if self.should_validate_body(validator) and not self._is_body_valid(resource):
            raise BadRequestBody(message="Invalid request body")

        return