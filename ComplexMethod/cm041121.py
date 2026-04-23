def patch_api_gateway_entity(entity: Any, patch_operations: ListOfPatchOperation):
    patch_operations = patch_operations or []

    if isinstance(entity, dict):
        entity_dict = entity
    else:
        if not isinstance(entity.__dict__, DelSafeDict):
            entity.__dict__ = DelSafeDict(entity.__dict__)
        entity_dict = entity.__dict__

    not_supported_attributes = {"/id", "/region_name", "/create_date"}

    model_attributes = list(entity_dict.keys())
    for operation in patch_operations:
        path_start = operation["path"].strip("/").split("/")[0]
        path_start_usc = camelcase_to_underscores(path_start)
        if path_start not in model_attributes and path_start_usc in model_attributes:
            operation["path"] = operation["path"].replace(path_start, path_start_usc)
        if operation["path"] in not_supported_attributes:
            raise BadRequestException(f"Invalid patch path {operation['path']}")

    apply_json_patch_safe(entity_dict, patch_operations, in_place=True)