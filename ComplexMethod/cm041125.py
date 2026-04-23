def update_resource(
        self,
        context: RequestContext,
        rest_api_id: String,
        resource_id: String,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> Resource:
        moto_rest_api = get_moto_rest_api(context, rest_api_id)
        moto_resource = moto_rest_api.resources.get(resource_id)
        if not moto_resource:
            raise NotFoundException("Invalid Resource identifier specified")

        store = get_apigateway_store(context=context)

        rest_api = store.rest_apis.get(rest_api_id)
        api_resources = rest_api.resource_children

        future_path_part = moto_resource.path_part
        current_parent_id = moto_resource.parent_id

        for patch_operation in patch_operations:
            op = patch_operation.get("op")
            if (path := patch_operation.get("path")) not in ("/pathPart", "/parentId"):
                raise BadRequestException(
                    f"Invalid patch path  '{path}' specified for op '{op}'. Must be one of: [/parentId, /pathPart]"
                )
            if op != "replace":
                raise BadRequestException(
                    f"Invalid patch path  '{path}' specified for op '{op}'. Please choose supported operations"
                )

            if moto_resource.parent_id is None:
                raise BadRequestException(f"Root resource cannot update its {path.strip('/')}.")

            if path == "/parentId":
                value = patch_operation.get("value")
                future_parent_resource = moto_rest_api.resources.get(value)
                if not future_parent_resource:
                    raise NotFoundException("Invalid Resource identifier specified")

                children_resources = api_resources.get(resource_id, [])
                if value in children_resources:
                    raise BadRequestException("Resources cannot be cyclical.")

                new_sibling_resources = api_resources.get(value, [])

            else:  # path == "/pathPart"
                future_path_part = patch_operation.get("value")
                new_sibling_resources = api_resources.get(moto_resource.parent_id, [])

            for sibling in new_sibling_resources:
                sibling_resource = moto_rest_api.resources[sibling]
                if sibling_resource.path_part == future_path_part:
                    raise ConflictException(
                        f"Another resource with the same parent already has this name: {future_path_part}"
                    )

        # TODO: test with multiple patch operations which would not be compatible between each other
        patch_api_gateway_entity(moto_resource, patch_operations)

        # after setting it, mutate the store
        if moto_resource.parent_id != current_parent_id:
            current_sibling_resources = api_resources.get(current_parent_id)
            if current_sibling_resources:
                current_sibling_resources.remove(resource_id)
                # if the parent does not have children anymore, remove from the list
                if not current_sibling_resources:
                    api_resources.pop(current_parent_id)

        # add it to the new parent children
        future_sibling_resources = api_resources.setdefault(moto_resource.parent_id, [])
        future_sibling_resources.append(resource_id)

        response = moto_resource.to_dict()
        return response