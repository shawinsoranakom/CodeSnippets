def update_stage(
        self,
        context: RequestContext,
        rest_api_id: String,
        stage_name: String,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> Stage:
        moto_rest_api = get_moto_rest_api(context, rest_api_id)
        if not (moto_stage := moto_rest_api.stages.get(stage_name)):
            raise NotFoundException("Invalid Stage identifier specified")

        # construct list of path regexes for validation
        path_regexes = [re.sub("{[^}]+}", ".+", path) for path in STAGE_UPDATE_PATHS]

        # copy the patch operations to not mutate them, so that we're logging the correct input
        patch_operations = copy.deepcopy(patch_operations) or []
        # we are only passing a subset of operations to Moto as it does not handle properly all of them
        moto_patch_operations = []
        moto_stage_copy = copy.deepcopy(moto_stage)
        for patch_operation in patch_operations:
            skip_moto_apply = False
            patch_path = patch_operation["path"]
            patch_op = patch_operation["op"]

            # special case: handle updates (op=remove) for wildcard method settings
            patch_path_stripped = patch_path.strip("/")
            if patch_path_stripped == "*/*" and patch_op == "remove":
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
            if is_canary := patch_path.startswith("/canarySettings"):
                skip_moto_apply = True
                path_valid = is_canary_settings_update_patch_valid(op=patch_op, path=patch_path)
                # it seems our JSON Patch utility does not handle replace properly if the value does not exist before
                # it seems to maybe be a Stage-only thing, so replacing it here
                if patch_op == "replace":
                    patch_operation["op"] = "add"
            elif patch_path.startswith("/accessLogSettings"):
                validate_access_log_settings_update_patch_valid(
                    op=patch_op, path=patch_path, value=patch_operation.get("value")
                )
                # for AccessLogSettings, Moto does support its patching, but does not support `add`, so we replace it
                if patch_op == "add":
                    patch_operation["op"] = "replace"

            if patch_op == "copy":
                copy_from = patch_operation.get("from")
                if patch_path not in ("/deploymentId", "/variables") or copy_from not in (
                    "/canarySettings/deploymentId",
                    "/canarySettings/stageVariableOverrides",
                ):
                    raise BadRequestException(
                        "Invalid copy operation with path: /canarySettings/stageVariableOverrides and from /variables. Valid copy:path are [/deploymentId, /variables] and valid copy:from are [/canarySettings/deploymentId, /canarySettings/stageVariableOverrides]"
                    )

                if copy_from.startswith("/canarySettings") and not getattr(
                    moto_stage_copy, "canary_settings", None
                ):
                    raise BadRequestException("Promotion not available. Canary does not exist.")

                if patch_path == "/variables":
                    moto_stage_copy.variables.update(
                        moto_stage_copy.canary_settings.get("stageVariableOverrides", {})
                    )
                elif patch_path == "/deploymentId":
                    moto_stage_copy.deployment_id = moto_stage_copy.canary_settings["deploymentId"]

                # we manually assign `copy` ops, no need to apply them
                continue

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

            elif patch_path in ("/canarySettings/deploymentId", "/deploymentId"):
                if patch_op != "copy" and not moto_rest_api.deployments.get(
                    patch_operation.get("value")
                ):
                    raise BadRequestException("Deployment id does not exist")

            if not skip_moto_apply:
                # we need to copy the patch operation because `_patch_api_gateway_entity` is mutating it in place
                moto_patch_operations.append(dict(patch_operation))

            # we need to apply patch operation individually to be able to validate the logic
            # TODO: rework the patching logic
            patch_api_gateway_entity(moto_stage_copy, [patch_operation])
            if is_canary and (canary_settings := getattr(moto_stage_copy, "canary_settings", None)):
                default_canary_settings = {
                    "deploymentId": moto_stage_copy.deployment_id,
                    "percentTraffic": 0.0,
                    "useStageCache": False,
                }
                default_canary_settings.update(canary_settings)
                default_canary_settings["percentTraffic"] = float(
                    default_canary_settings["percentTraffic"]
                )
                moto_stage_copy.canary_settings = default_canary_settings

        moto_rest_api.stages[stage_name] = moto_stage_copy
        moto_stage_copy.apply_operations(moto_patch_operations)
        if moto_stage.deployment_id != moto_stage_copy.deployment_id:
            store = get_apigateway_store(context=context)
            store.active_deployments.setdefault(rest_api_id.lower(), {})[stage_name] = (
                moto_stage_copy.deployment_id
            )

        moto_stage_copy.last_updated_date = datetime.datetime.now(tz=datetime.UTC)

        response = moto_stage_copy.to_json()
        self._patch_stage_response(response)
        return response