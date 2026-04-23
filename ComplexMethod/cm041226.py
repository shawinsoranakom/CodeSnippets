def provision(self, skip_deployment: bool | None = False):
        """
        Execute all previously added custom provisioning steps and deploy added CDK stacks via CloudFormation.

        Already deployed stacks will be updated instead.
        """
        self._synth()
        if skip_deployment:
            LOG.debug("Skipping deployment. Assuming stacks have already been created")
            return

        is_update = False

        if all(
            self._is_stack_deployed(stack_name, stack)
            for stack_name, stack in self.cloudformation_stacks.items()
        ):
            LOG.debug("All stacks are already deployed. Skipping the provisioning.")
            # TODO: in localstack we might want to do a delete/create
            #  but generally this won't be a common use case when developing against LocalStack
            is_update = True

        self._bootstrap()
        self._run_manual_setup_tasks()
        for stack_name, stack in self.cloudformation_stacks.items():
            change_set_name = f"test-cs-{short_uid()}"
            if len(stack["Template"]) > CFN_MAX_TEMPLATE_SIZE:
                # if the template size is too big, we need to upload it to s3 first
                # and use TemplateURL instead to point to the template in s3
                template_bucket_name = self._template_bucket_name()
                self._create_bucket_if_not_exists(template_bucket_name)
                key = f"{stack_name}.yaml"
                self.aws_client.s3.put_object(
                    Bucket=template_bucket_name, Key=key, Body=stack["Template"]
                )
                url = self.aws_client.s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": template_bucket_name, "Key": key},
                    ExpiresIn=10,
                )

                change_set = self.aws_client.cloudformation.create_change_set(
                    StackName=stack_name,
                    ChangeSetName=change_set_name,
                    TemplateURL=url,
                    ChangeSetType="UPDATE" if is_update else "CREATE",
                    Capabilities=[
                        Capability.CAPABILITY_AUTO_EXPAND,
                        Capability.CAPABILITY_IAM,
                        Capability.CAPABILITY_NAMED_IAM,
                    ],
                )
            else:
                change_set = self.aws_client.cloudformation.create_change_set(
                    StackName=stack_name,
                    ChangeSetName=change_set_name,
                    TemplateBody=stack["Template"],
                    ChangeSetType="UPDATE" if is_update else "CREATE",
                    Capabilities=[
                        Capability.CAPABILITY_AUTO_EXPAND,
                        Capability.CAPABILITY_IAM,
                        Capability.CAPABILITY_NAMED_IAM,
                    ],
                )
            stack_id = self.cloudformation_stacks[stack_name]["StackId"] = change_set["StackId"]
            try:
                self.aws_client.cloudformation.get_waiter("change_set_create_complete").wait(
                    ChangeSetName=change_set["Id"],
                    WaiterConfig=WAITER_CONFIG_AWS if is_aws_cloud() else WAITER_CONFIG_LS,
                )
            except WaiterError:
                # it's OK if we don't have any updates to perform here (!)
                # there is no specific error code unfortunately
                if not (is_update):
                    raise
                else:
                    LOG.warning("Execution of change set %s failed. Assuming no changes detected.")
            else:
                self.aws_client.cloudformation.execute_change_set(ChangeSetName=change_set["Id"])
                try:
                    self.aws_client.cloudformation.get_waiter(
                        "stack_update_complete" if is_update else "stack_create_complete"
                    ).wait(
                        StackName=stack_id,
                        WaiterConfig=WAITER_CONFIG_AWS if is_aws_cloud() else WAITER_CONFIG_LS,
                    )

                except WaiterError as e:
                    raise StackDeployError(
                        self.aws_client.cloudformation.describe_stacks(StackName=stack_id)[
                            "Stacks"
                        ][0],
                        self.aws_client.cloudformation.describe_stack_events(StackName=stack_id)[
                            "StackEvents"
                        ],
                    ) from e

            if stack["AutoCleanS3"]:
                stack_resources = self.aws_client.cloudformation.describe_stack_resources(
                    StackName=stack_id
                )["StackResources"]
                s3_buckets = [
                    r["PhysicalResourceId"]
                    for r in stack_resources
                    if r["ResourceType"] == "AWS::S3::Bucket"
                ]

                for s3_bucket in s3_buckets:
                    self.custom_cleanup_steps.append(
                        lambda bucket=s3_bucket: cleanup_s3_bucket(
                            self.aws_client.s3, bucket, delete_bucket=False
                        )
                    )