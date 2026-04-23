def secretsmanager_api():
        return [
            KeyValueBasedTransformer(
                lambda k, v: (
                    k
                    if (isinstance(k, str) and isinstance(v, list) and re.match(PATTERN_UUID, k))
                    else None
                ),
                "version_uuid",
            ),
            KeyValueBasedTransformer(
                lambda k, v: (
                    v
                    if (
                        isinstance(k, str)
                        and k == "VersionId"
                        and isinstance(v, str)
                        and re.match(PATTERN_UUID, v)
                    )
                    else None
                ),
                "version_uuid",
            ),
            KeyValueBasedTransformer(
                lambda k, v: (
                    v
                    if (
                        isinstance(k, str)
                        and k == "RotationLambdaARN"
                        and isinstance(v, str)
                        and re.match(PATTERN_ARN, v)
                    )
                    else None
                ),
                "lambda-arn",
            ),
            SortingTransformer("VersionStages"),
            SortingTransformer("Versions", lambda e: e.get("CreatedDate")),
        ]