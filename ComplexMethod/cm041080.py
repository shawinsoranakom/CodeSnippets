def _invoke_macro(self, name: str, parameters: dict, fragment: dict, allow_string=False):
        account_id = self._change_set.account_id
        region_name = self._change_set.region_name
        macro_definition = get_cloudformation_store(
            account_id=account_id, region_name=region_name
        ).macros.get(name)

        if not macro_definition:
            raise FailedTransformationException(name, f"Transformation {name} is not supported.")

        simplified_parameters = {}
        if resolved_parameters := self._change_set.resolved_parameters:
            for key, resolved_parameter in resolved_parameters.items():
                final_value = engine_parameter_value(resolved_parameter)
                simplified_parameters[key] = (
                    final_value.split(",")
                    if resolved_parameter["type_"] == "CommaDelimitedList"
                    else final_value
                )

        transformation_id = f"{account_id}::{name}"
        event = {
            "region": region_name,
            "accountId": account_id,
            "fragment": fragment,
            "transformId": transformation_id,
            "params": parameters,
            "requestId": long_uid(),
            "templateParameterValues": simplified_parameters,
        }

        client = connect_to(aws_access_key_id=account_id, region_name=region_name).lambda_
        try:
            invocation = client.invoke(
                FunctionName=macro_definition["FunctionName"], Payload=json.dumps(event)
            )
        except ClientError:
            LOG.error(
                "client error executing lambda function '%s' with payload '%s'",
                macro_definition["FunctionName"],
                json.dumps(event),
            )
            raise
        if invocation.get("StatusCode") != 200 or invocation.get("FunctionError") == "Unhandled":
            raise FailedTransformationException(
                transformation=name,
                message=f"Received malformed response from transform {transformation_id}. Rollback requested by user.",
            )
        result = json.loads(invocation["Payload"].read())

        if result.get("status") != "success":
            error_message = result.get("errorMessage")
            message = (
                f"Transform {transformation_id} failed with: {error_message}. Rollback requested by user."
                if error_message
                else f"Transform {transformation_id} failed without an error message.. Rollback requested by user."
            )
            raise FailedTransformationException(transformation=name, message=message)

        if not isinstance(result.get("fragment"), dict) and not allow_string:
            raise FailedTransformationException(
                transformation=name,
                message="Template format error: unsupported structure.. Rollback requested by user.",
            )

        return result.get("fragment")