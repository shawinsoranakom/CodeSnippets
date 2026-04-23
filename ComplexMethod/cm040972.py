def create(
        self,
        request: ResourceRequest[OpenSearchServiceDomainProperties],
    ) -> ProgressEvent[OpenSearchServiceDomainProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/DomainName



        Create-only properties:
          - /properties/DomainName

        Read-only properties:
          - /properties/Id
          - /properties/Arn
          - /properties/DomainArn
          - /properties/DomainEndpoint
          - /properties/DomainEndpoints
          - /properties/ServiceSoftwareOptions
          - /properties/AdvancedSecurityOptions/AnonymousAuthDisableDate

        IAM permissions required:
          - es:CreateDomain
          - es:DescribeDomain
          - es:AddTags
          - es:ListTags

        """
        model = request.desired_state
        opensearch_client = request.aws_client_factory.opensearch
        if not request.custom_context.get(REPEATED_INVOCATION):
            # resource is not ready
            # this is the first time this callback is invoked
            request.custom_context[REPEATED_INVOCATION] = True

            # defaults
            domain_name = model.get("DomainName")
            if not domain_name:
                domain_name = util.generate_default_name(
                    request.stack_name, request.logical_resource_id
                ).lower()[0:28]
                model["DomainName"] = domain_name

            properties = util.remove_none_values(model)
            cluster_config = properties.get("ClusterConfig")
            if isinstance(cluster_config, dict):
                # set defaults required for boto3 calls
                cluster_config.setdefault("DedicatedMasterType", "m3.medium.search")
                cluster_config.setdefault("WarmType", "ultrawarm1.medium.search")

                for key in ["DedicatedMasterCount", "InstanceCount", "WarmCount"]:
                    if key in cluster_config and isinstance(cluster_config[key], str):
                        cluster_config[key] = int(cluster_config[key])

            if properties.get("AccessPolicies"):
                properties["AccessPolicies"] = json.dumps(properties["AccessPolicies"])

            if ebs_options := properties.get("EBSOptions"):
                for key in ["Iops", "Throughput", "VolumeSize"]:
                    if key in ebs_options and isinstance(ebs_options[key], str):
                        ebs_options[key] = int(ebs_options[key])

            create_kwargs = {**util.deselect_attributes(properties, ["Tags"])}
            if tags := properties.get("Tags"):
                create_kwargs["TagList"] = tags
            opensearch_client.create_domain(**create_kwargs)
            return ProgressEvent(
                status=OperationStatus.IN_PROGRESS,
                resource_model=model,
                custom_context=request.custom_context,
            )
        opensearch_domain = opensearch_client.describe_domain(DomainName=model["DomainName"])
        if opensearch_domain["DomainStatus"]["Processing"] is False:
            # set data
            model["Arn"] = opensearch_domain["DomainStatus"]["ARN"]
            model["Id"] = opensearch_domain["DomainStatus"]["DomainId"]
            model["DomainArn"] = opensearch_domain["DomainStatus"]["ARN"]
            model["DomainEndpoint"] = opensearch_domain["DomainStatus"].get("Endpoint")
            model["DomainEndpoints"] = opensearch_domain["DomainStatus"].get("Endpoints")
            model["ServiceSoftwareOptions"] = opensearch_domain["DomainStatus"].get(
                "ServiceSoftwareOptions"
            )
            model.setdefault("AdvancedSecurityOptions", {})["AnonymousAuthDisableDate"] = (
                opensearch_domain["DomainStatus"]
                .get("AdvancedSecurityOptions", {})
                .get("AnonymousAuthDisableDate")
            )

            return ProgressEvent(status=OperationStatus.SUCCESS, resource_model=model)
        else:
            return ProgressEvent(status=OperationStatus.IN_PROGRESS, resource_model=model)