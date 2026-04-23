def update_model(
        self,
        context: RequestContext,
        rest_api_id: String,
        model_name: String,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> Model:
        # manually update the model, not need for JSON patch, only 2 path supported with replace operation
        # /schema
        # /description
        store = get_apigateway_store(context=context)
        if rest_api_id not in store.rest_apis or not (
            model := store.rest_apis[rest_api_id].models.get(model_name)
        ):
            raise NotFoundException(f"Invalid model name specified: {model_name}")

        for operation in patch_operations:
            path = operation.get("path")
            if operation.get("op") != "replace":
                raise BadRequestException(
                    f"Invalid patch path  '{path}' specified for op 'add'. Please choose supported operations"
                )
            if path not in ("/schema", "/description"):
                raise BadRequestException(
                    f"Invalid patch path  '{path}' specified for op 'replace'. Must be one of: [/description, /schema]"
                )

            key = path[1:]  # remove the leading slash
            value = operation.get("value")
            if key == "schema":
                if not value:
                    raise BadRequestException(
                        "Model schema must have at least 1 property or array items defined"
                    )
                # delete the resolved model to invalidate it
                store.rest_apis[rest_api_id].resolved_models.pop(model_name, None)
            model[key] = value
        remove_empty_attributes_from_model(model)
        return model