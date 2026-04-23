def _validate_destination_config(
        self, store: LambdaStore, function_name: str, destination_config: DestinationConfig
    ):
        def _validate_destination_arn(destination_arn) -> bool:
            if not api_utils.DESTINATION_ARN_PATTERN.match(destination_arn):
                # technically we shouldn't handle this in the provider
                raise ValidationException(
                    "1 validation error detected: Value '"
                    + destination_arn
                    + "' at 'destinationConfig.onFailure.destination' failed to satisfy constraint: Member must satisfy regular expression pattern: "
                    + "$|kafka://([^.]([a-zA-Z0-9\\-_.]{0,248}))|arn:(aws[a-zA-Z0-9-]*):([a-zA-Z0-9\\-])+:((eusc-)?[a-z]{2}((-gov)|(-iso([a-z]?)))?-[a-z]+-\\d{1})?:(\\d{12})?:(.*)"
                )

            match destination_arn.split(":")[2]:
                case "lambda":
                    fn_parts = api_utils.FULL_FN_ARN_PATTERN.search(destination_arn).groupdict()
                    if fn_parts:
                        # check if it exists
                        fn = store.functions.get(fn_parts["function_name"])
                        if not fn:
                            raise InvalidParameterValueException(
                                f"The destination ARN {destination_arn} is invalid.", Type="User"
                            )
                        if fn_parts["function_name"] == function_name:
                            raise InvalidParameterValueException(
                                "You can't specify the function as a destination for itself.",
                                Type="User",
                            )
                case "sns" | "sqs" | "events":
                    pass
                case _:
                    return False
            return True

        validation_err = False

        failure_destination = destination_config.get("OnFailure", {}).get("Destination")
        if failure_destination:
            validation_err = validation_err or not _validate_destination_arn(failure_destination)

        success_destination = destination_config.get("OnSuccess", {}).get("Destination")
        if success_destination:
            validation_err = validation_err or not _validate_destination_arn(success_destination)

        if validation_err:
            on_success_part = (
                f"OnSuccess(destination={success_destination})" if success_destination else "null"
            )
            on_failure_part = (
                f"OnFailure(destination={failure_destination})" if failure_destination else "null"
            )
            raise InvalidParameterValueException(
                f"The provided destination config DestinationConfig(onSuccess={on_success_part}, onFailure={on_failure_part}) is invalid.",
                Type="User",
            )