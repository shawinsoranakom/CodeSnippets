def _get_resources_and_snapshot(
        rest_api_id: str, resources: Resources, snapshot_prefix: str = ""
    ):
        """

        :param rest_api_id: The RestAPI ID
        :param resources: the response from GetResources
        :param snapshot_prefix: optional snapshot prefix for every snapshot
        :return:
        """
        for resource in resources["items"]:
            for http_method in resource.get("resourceMethods", []):
                snapshot_http_key = f"{resource['path'][1:] if resource['path'] != '/' else 'root'}-{http_method.lower()}"
                resource_id = resource["id"]
                try:
                    response = aws_client.apigateway.get_method(
                        restApiId=rest_api_id,
                        resourceId=resource_id,
                        httpMethod=http_method,
                    )
                    snapshot.match(f"{snapshot_prefix}method-{snapshot_http_key}", response)
                except ClientError as e:
                    snapshot.match(f"{snapshot_prefix}method-{snapshot_http_key}", e.response)

                try:
                    response = aws_client.apigateway.get_method_response(
                        restApiId=rest_api_id,
                        resourceId=resource_id,
                        httpMethod=http_method,
                        statusCode="200",
                    )
                    snapshot.match(
                        f"{snapshot_prefix}method-response-{snapshot_http_key}", response
                    )
                except ClientError as e:
                    snapshot.match(
                        f"{snapshot_prefix}method-response-{snapshot_http_key}", e.response
                    )

                try:
                    response = aws_client.apigateway.get_integration(
                        restApiId=rest_api_id,
                        resourceId=resource_id,
                        httpMethod=http_method,
                    )
                    snapshot.match(f"{snapshot_prefix}integration-{snapshot_http_key}", response)
                except ClientError as e:
                    snapshot.match(f"{snapshot_prefix}integration-{snapshot_http_key}", e.response)

                try:
                    response = aws_client.apigateway.get_integration_response(
                        restApiId=rest_api_id,
                        resourceId=resource_id,
                        httpMethod=http_method,
                        statusCode="200",
                    )
                    snapshot.match(
                        f"{snapshot_prefix}integration-response-{snapshot_http_key}", response
                    )
                except ClientError as e:
                    snapshot.match(
                        f"{snapshot_prefix}integration-response-{snapshot_http_key}", e.response
                    )