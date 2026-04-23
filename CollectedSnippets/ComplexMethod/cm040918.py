def _validate_notification(self, verification_ctx: BucketVerificationContext):
        """
        Validates the notification configuration
        - setting default ID if not provided
        - validate the arn pattern
        - validating the Rule names (and normalizing to capitalized)
        - check if the filter value is not empty
        :param verification_ctx: the verification context containing necessary data for validation
        :raises InvalidArgument if the rule is not valid, infos in ArgumentName and ArgumentValue members
        :return:
        """
        configuration = verification_ctx.configuration
        # id's can be set the request, but need to be auto-generated if they are not provided
        if not configuration.get("Id"):
            configuration["Id"] = short_uid()

        arn, argument_name = self._get_arn_value_and_name(configuration)

        if not re.match(f"{ARN_PARTITION_REGEX}:{self.service_name}:", arn):
            raise InvalidArgument(
                "The ARN could not be parsed",
                ArgumentName=argument_name,
                ArgumentValue=arn,
            )

        if not verification_ctx.skip_destination_validation:
            self._verify_target(arn, verification_ctx)

        if filter_rules := configuration.get("Filter", {}).get("Key", {}).get("FilterRules"):
            for rule in filter_rules:
                if "Name" not in rule or "Value" not in rule:
                    raise MalformedXML()

                if rule["Name"].lower() not in ["suffix", "prefix"]:
                    raise InvalidArgument(
                        "filter rule name must be either prefix or suffix",
                        ArgumentName="FilterRule.Name",
                        ArgumentValue=rule["Name"],
                    )

                rule["Name"] = rule["Name"].capitalize()