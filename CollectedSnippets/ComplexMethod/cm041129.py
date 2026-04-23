def update_stage(
        self,
        context: RequestContext,
        rest_api_id: String,
        stage_name: String,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> Stage:
        call_moto(context)

        moto_backend = get_moto_backend(context.account_id, context.region)
        moto_rest_api: MotoRestAPI = moto_backend.apis.get(rest_api_id)
        if not (moto_stage := moto_rest_api.stages.get(stage_name)):
            raise NotFoundException("Invalid Stage identifier specified")

        # construct list of path regexes for validation
        path_regexes = [re.sub("{[^}]+}", ".+", path) for path in STAGE_UPDATE_PATHS]

        # copy the patch operations to not mutate them, so that we're logging the correct input
        patch_operations = copy.deepcopy(patch_operations) or []
        for patch_operation in patch_operations:
            patch_path = patch_operation["path"]

            # special case: handle updates (op=remove) for wildcard method settings
            patch_path_stripped = patch_path.strip("/")
            if patch_path_stripped == "*/*" and patch_operation["op"] == "remove":
                if not moto_stage.method_settings.pop(patch_path_stripped, None):
                    raise BadRequestException(
                        "Cannot remove method setting */* because there is no method setting for this method "
                    )
                response = moto_stage.to_json()
                self._patch_stage_response(response)
                return response

            path_valid = patch_path in STAGE_UPDATE_PATHS or any(
                re.match(regex, patch_path) for regex in path_regexes
            )
            if not path_valid:
                valid_paths = f"[{', '.join(STAGE_UPDATE_PATHS)}]"
                # note: weird formatting in AWS - required for snapshot testing
                valid_paths = valid_paths.replace(
                    "/{resourcePath}/{httpMethod}/throttling/burstLimit, /{resourcePath}/{httpMethod}/throttling/rateLimit, /{resourcePath}/{httpMethod}/caching/ttlInSeconds",
                    "/{resourcePath}/{httpMethod}/throttling/burstLimit/{resourcePath}/{httpMethod}/throttling/rateLimit/{resourcePath}/{httpMethod}/caching/ttlInSeconds",
                )
                valid_paths = valid_paths.replace("/burstLimit, /", "/burstLimit /")
                valid_paths = valid_paths.replace("/rateLimit, /", "/rateLimit /")
                raise BadRequestException(
                    f"Invalid method setting path: {patch_operation['path']}. Must be one of: {valid_paths}"
                )

            # TODO: check if there are other boolean, maybe add a global step in _patch_api_gateway_entity
            if patch_path == "/tracingEnabled" and (value := patch_operation.get("value")):
                patch_operation["value"] = value and value.lower() == "true" or False

        patch_api_gateway_entity(moto_stage, patch_operations)
        moto_stage.apply_operations(patch_operations)

        response = moto_stage.to_json()
        self._patch_stage_response(response)
        return response