def validate_request(
        self, method: Method, rest_api: RestApiContainer, request: InvocationRequest
    ) -> None:
        """
        :raises BadRequestParametersError if the request has required parameters which are not present
        :raises BadRequestBodyError if the request has required body validation with a model and it does not respect it
        :return: None
        """

        # check if there is validator for the method
        if not (request_validator_id := method.get("requestValidatorId") or "").strip():
            return

        # check if there is a validator for this request
        if not (validator := rest_api.validators.get(request_validator_id)):
            # TODO Should we raise an exception instead?
            LOG.error(
                "No validator were found with matching id: '%s'",
                request_validator_id,
                exc_info=LOG.isEnabledFor(logging.DEBUG),
            )
            return

        if self.should_validate_request(validator) and (
            missing_parameters := self._get_missing_required_parameters(method, request)
        ):
            message = f"Missing required request parameters: [{', '.join(missing_parameters)}]"
            raise BadRequestParametersError(message=message)

        if self.should_validate_body(validator) and not self._is_body_valid(
            method, rest_api, request
        ):
            raise BadRequestBodyError(message="Invalid request body")

        return