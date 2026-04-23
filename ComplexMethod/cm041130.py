def update_documentation_part(
        self,
        context: RequestContext,
        rest_api_id: String,
        documentation_part_id: String,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> DocumentationPart:
        # TODO: add validation
        store = get_apigateway_store(context=context)
        rest_api_container = store.rest_apis.get(rest_api_id)
        # TODO: validate the restAPI id to remove the conditional
        doc_part = (
            rest_api_container.documentation_parts.get(documentation_part_id)
            if rest_api_container
            else None
        )

        if doc_part is None:
            raise NotFoundException("Invalid Documentation part identifier specified")

        for patch_operation in patch_operations:
            path = patch_operation.get("path")
            operation = patch_operation.get("op")
            if operation != "replace":
                raise BadRequestException(
                    f"Invalid patch path  '{path}' specified for op '{operation}'. "
                    f"Please choose supported operations"
                )

            if path != "/properties":
                raise BadRequestException(
                    f"Invalid patch path  '{path}' specified for op 'replace'. "
                    f"Must be one of: [/properties]"
                )

            key = path[1:]
            if key == "properties" and not patch_operation.get("value"):
                raise BadRequestException("Documentation part properties must be non-empty")

        patched_doc_part = apply_json_patch_safe(doc_part, patch_operations)

        rest_api_container.documentation_parts[documentation_part_id] = patched_doc_part

        return to_documentation_part_response_json(rest_api_id, patched_doc_part)