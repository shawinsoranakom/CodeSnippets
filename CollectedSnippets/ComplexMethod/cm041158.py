def create_deployment(
        self,
        context: RequestContext,
        rest_api_id: String,
        stage_name: String = None,
        stage_description: String = None,
        description: String = None,
        cache_cluster_enabled: NullableBoolean = None,
        cache_cluster_size: CacheClusterSize = None,
        variables: MapOfStringToString = None,
        canary_settings: DeploymentCanarySettings = None,
        tracing_enabled: NullableBoolean = None,
        **kwargs,
    ) -> Deployment:
        moto_rest_api = get_moto_rest_api(context, rest_api_id)
        if canary_settings:
            # TODO: add validation to the canary settings
            if not stage_name:
                error_stage = stage_name if stage_name is not None else "null"
                raise BadRequestException(
                    f"Invalid deployment content specified.Non null and non empty stageName must be provided for canary deployment. Provided value is {error_stage}"
                )
            if stage_name not in moto_rest_api.stages:
                raise BadRequestException(
                    "Invalid deployment content specified.Stage non-existing must already be created before making a canary release deployment"
                )

        # FIXME: moto has an issue and is not handling canarySettings, hence overwriting the current stage with the
        #  canary deployment
        current_stage = None
        if stage_name:
            current_stage = copy.deepcopy(moto_rest_api.stages.get(stage_name))

        # TODO: if the REST API does not contain any method, we should raise an exception
        deployment: Deployment = call_moto(context)
        # https://docs.aws.amazon.com/apigateway/latest/developerguide/updating-api.html
        # TODO: the deployment is not accessible until it is linked to a stage
        # you can combine a stage or later update the deployment with a stage id
        store = get_apigateway_store(context=context)
        rest_api_container = get_rest_api_container(context, rest_api_id=rest_api_id)
        frozen_deployment = freeze_rest_api(
            account_id=context.account_id,
            region=context.region,
            moto_rest_api=moto_rest_api,
            localstack_rest_api=rest_api_container,
        )
        router_api_id = rest_api_id.lower()
        deployment_id = deployment["id"]
        store.internal_deployments.setdefault(router_api_id, {})[deployment_id] = frozen_deployment

        if stage_name:
            moto_stage = moto_rest_api.stages[stage_name]
            if canary_settings:
                moto_stage = current_stage
                moto_rest_api.stages[stage_name] = current_stage

                default_settings = {
                    "deploymentId": deployment_id,
                    "percentTraffic": 0.0,
                    "useStageCache": False,
                }
                default_settings.update(canary_settings)
                moto_stage.canary_settings = default_settings
            else:
                store.active_deployments.setdefault(router_api_id, {})[stage_name] = deployment_id
                moto_stage.canary_settings = None

            if variables:
                moto_stage.variables = variables

            moto_stage.description = stage_description or moto_stage.description or None

            if cache_cluster_enabled is not None:
                moto_stage.cache_cluster_enabled = cache_cluster_enabled

            if cache_cluster_size is not None:
                moto_stage.cache_cluster_size = cache_cluster_size

            if tracing_enabled is not None:
                moto_stage.tracing_enabled = tracing_enabled

        return deployment