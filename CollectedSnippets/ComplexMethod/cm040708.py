def update_function_code(
        self, context: RequestContext, request: UpdateFunctionCodeRequest
    ) -> FunctionConfiguration:
        """updates the $LATEST version of the function"""
        # only supports normal zip packaging atm
        # if request.get("Publish"):
        #     self.lambda_service.create_function_version()

        function_name = request.get("FunctionName")
        account_id, region = api_utils.get_account_and_region(function_name, context)
        function_name, qualifier = api_utils.get_name_and_qualifier(function_name, None, context)

        store = lambda_stores[account_id][region]
        if function_name not in store.functions:
            raise ResourceNotFoundException(
                f"Function not found: {api_utils.unqualified_lambda_arn(function_name=function_name, region=region, account=account_id)}",
                Type="User",
            )
        function = store.functions[function_name]

        revision_id = request.get("RevisionId")
        if revision_id and revision_id != function.latest().config.revision_id:
            raise PreconditionFailedException(
                "The Revision Id provided does not match the latest Revision Id. "
                "Call the GetFunction/GetAlias API to retrieve the latest Revision Id",
                Type="User",
            )

        # TODO verify if correct combination of code is set
        image = None
        if (
            request.get("ZipFile") or request.get("S3Bucket")
        ) and function.latest().config.package_type == PackageType.Image:
            raise InvalidParameterValueException(
                "Please provide ImageUri when updating a function with packageType Image.",
                Type="User",
            )
        elif request.get("ImageUri") and function.latest().config.package_type == PackageType.Zip:
            raise InvalidParameterValueException(
                "Please don't provide ImageUri when updating a function with packageType Zip.",
                Type="User",
            )

        if publish_to := request.get("PublishTo"):
            self._validate_publish_to(publish_to)

        if zip_file := request.get("ZipFile"):
            code = store_lambda_archive(
                archive_file=zip_file,
                function_name=function_name,
                region_name=region,
                account_id=account_id,
            )
        elif s3_bucket := request.get("S3Bucket"):
            s3_key = request["S3Key"]
            s3_object_version = request.get("S3ObjectVersion")
            code = store_s3_bucket_archive(
                archive_bucket=s3_bucket,
                archive_key=s3_key,
                archive_version=s3_object_version,
                function_name=function_name,
                region_name=region,
                account_id=account_id,
            )
        elif image := request.get("ImageUri"):
            code = None
            image = create_image_code(image_uri=image)
        else:
            raise LambdaServiceException("A ZIP file, S3 bucket, or image is required")

        old_function_version = function.versions.get("$LATEST")
        replace_kwargs = {"code": code} if code else {"image": image}

        if architectures := request.get("Architectures"):
            if len(architectures) != 1:
                raise ValidationException(
                    f"1 validation error detected: Value '[{', '.join(architectures)}]' at 'architectures' failed to "
                    f"satisfy constraint: Member must have length less than or equal to 1",
                )
            # An empty list of architectures is also forbidden. Further exceptions are tested here for create_function:
            # tests.aws.services.lambda_.test_lambda_api.TestLambdaFunction.test_create_lambda_exceptions
            if architectures[0] not in ARCHITECTURES:
                raise ValidationException(
                    f"1 validation error detected: Value '[{', '.join(architectures)}]' at 'architectures' failed to "
                    f"satisfy constraint: Member must satisfy constraint: [Member must satisfy enum value set: "
                    f"[x86_64, arm64], Member must not be null]",
                )
            replace_kwargs["architectures"] = architectures

        config = dataclasses.replace(
            old_function_version.config,
            internal_revision=short_uid(),
            last_modified=api_utils.generate_lambda_date(),
            last_update=UpdateStatus(
                status=LastUpdateStatus.InProgress,
                code="Creating",
                reason="The function is being created.",
            ),
            **replace_kwargs,
        )
        function_version = dataclasses.replace(old_function_version, config=config)
        function.versions["$LATEST"] = function_version

        self.lambda_service.update_version(new_version=function_version)
        if request.get("Publish"):
            function_version = self._publish_version_with_changes(
                function_name=function_name,
                region=region,
                account_id=account_id,
                publish_to=publish_to,
                is_active=True,
            )
        return api_utils.map_config_out(
            function_version, return_qualified_arn=bool(request.get("Publish"))
        )