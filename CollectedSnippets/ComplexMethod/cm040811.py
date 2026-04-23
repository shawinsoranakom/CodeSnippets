def validate_targets_input(self, targets: TargetList) -> PutTargetsResultEntryList:
        validation_errors = []
        for index, target in enumerate(targets):
            id = target.get("Id")
            arn = target.get("Arn", "")
            if not TARGET_ID_REGEX.match(id):
                validation_errors.append(
                    {
                        "TargetId": id,
                        "ErrorCode": "ValidationException",
                        "ErrorMessage": f"Value '{id}' at 'targets.{index + 1}.member.id' failed to satisfy constraint: Member must satisfy regular expression pattern: [\\.\\-_A-Za-z0-9]+",
                    }
                )

            if len(id) > 64:
                validation_errors.append(
                    {
                        "TargetId": id,
                        "ErrorCode": "ValidationException",
                        "ErrorMessage": f"Value '{id}' at 'targets.{index + 1}.member.id' failed to satisfy constraint: Member must have length less than or equal to 64",
                    }
                )

            if not TARGET_ARN_REGEX.match(arn):
                validation_errors.append(
                    {
                        "TargetId": id,
                        "ErrorCode": "ValidationException",
                        "ErrorMessage": f"Parameter {arn} is not valid. Reason: Provided Arn is not in correct format.",
                    }
                )

            if ":sqs:" in arn and arn.endswith(".fifo") and not target.get("SqsParameters"):
                validation_errors.append(
                    {
                        "TargetId": id,
                        "ErrorCode": "ValidationException",
                        "ErrorMessage": f"Parameter(s) SqsParameters must be specified for target: {id}.",
                    }
                )

        return validation_errors