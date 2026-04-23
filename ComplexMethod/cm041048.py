def available_schemas(self, pattern: str) -> list[str]:
        """
        Return the names of available CloudFormation resource types. `pattern` should be something like
        AWS::S3::Bucket or AWS::S3::*, depending on whether you want all resources for a service or a specific one.
        The result is a list of matching resource type names (e.g. [AWS::S3::Bucket, AWS::S3::Object, ...])
        """

        is_wildcard = pattern.endswith("*")
        pattern = pattern[:-1] if is_wildcard else pattern
        matching_names = []

        params = {
            "Visibility": "PUBLIC",
            "Type": "RESOURCE",
            "DeprecatedStatus": "LIVE",
            "Filters": {"Category": "AWS_TYPES", "TypeNamePrefix": pattern},
        }
        next_token: str | None = None

        # Note: pagination is necessary since list_types requires multiple calls even to get a single result.
        while True:
            if next_token:
                params["NextToken"] = next_token
            response = self.cfn_client.list_types(**params)

            # collect any matching type names (if wildcard, all; else exact match only)
            matching_names.extend(
                [
                    type_summary["TypeName"]
                    for type_summary in response.get("TypeSummaries", [])
                    if (is_wildcard or type_summary["TypeName"] == pattern)
                ]
            )

            next_token = response.get("NextToken")
            if not next_token:
                break

        return matching_names