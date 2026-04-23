def setup_and_teardown(self, aws_client, region_name, delenv, get_deployed_stage):
        if not is_aws_cloud():
            delenv("AWS_PROFILE", raising=False)
        base_dir = get_base_dir()
        if not os.path.exists(os.path.join(base_dir, "node_modules")):
            # install dependencies
            run(["npm", "install"], cwd=base_dir)

        # list apigateway before sls deployment
        apis = aws_client.apigateway.get_rest_apis()["items"]
        existing_api_ids = [api["id"] for api in apis]

        # deploy serverless app
        if is_aws_cloud():
            run(
                ["npm", "run", "deploy-aws", "--", f"--region={region_name}"],
                cwd=base_dir,
            )
        else:
            run(
                ["npm", "run", "deploy", "--", f"--region={region_name}"],
                cwd=base_dir,
                env_vars={"AWS_ACCESS_KEY_ID": TEST_AWS_ACCESS_KEY_ID},
            )

        yield existing_api_ids

        try:
            # cleanup s3 bucket content
            bucket_name = f"testing-bucket-sls-test-{get_deployed_stage}-{region_name}"
            response = aws_client.s3.list_objects_v2(Bucket=bucket_name)
            objects = [{"Key": obj["Key"]} for obj in response.get("Contents", [])]
            if objects:
                aws_client.s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={"Objects": objects},
                )
            # TODO the cleanup still fails due to inability to find ECR service in community
            command = "undeploy-aws" if is_aws_cloud() else "undeploy"
            run(["npm", "run", command, "--", f"--region={region_name}"], cwd=base_dir)
        except Exception:
            LOG.error("Unable to clean up serverless stack")