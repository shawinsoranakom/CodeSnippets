def get(canvas_id):
    if not UserCanvasService.accessible(canvas_id, current_user.id):
        return get_data_error_result(message="canvas not found.")
    e, c = UserCanvasService.get_by_canvas_id(canvas_id)
    if not e:
        return get_data_error_result(message="canvas not found.")
    try:
        # DELETE
        CanvasReplicaService.bootstrap(
            canvas_id=canvas_id,
            tenant_id=str(current_user.id),
            runtime_user_id=str(current_user.id),
            dsl=c.get("dsl"),
            canvas_category=c.get("canvas_category", CanvasCategory.Agent),
            title=c.get("title", ""),
        )
    except ValueError as e:
        return get_data_error_result(message=str(e))

    # Get the last publication time (latest released version's update_time)
    last_publish_time = None
    versions = UserCanvasVersionService.list_by_canvas_id(canvas_id)
    if versions:
        released_versions = [v for v in versions if v.release]
        if released_versions:
            # Sort by update_time descending and get the latest
            released_versions.sort(key=lambda x: x.update_time, reverse=True)
            last_publish_time = released_versions[0].update_time

    # Add last_publish_time to response data
    if isinstance(c, dict):
        c["dsl"] = normalize_chunker_dsl(c.get("dsl", {}))
        c["last_publish_time"] = last_publish_time
    else:
        # If c is a model object, convert to dict first
        c = c.to_dict()
        c["dsl"] = normalize_chunker_dsl(c.get("dsl", {}))
        c["last_publish_time"] = last_publish_time

    # For pipeline type, get associated datasets
    if c.get("canvas_category") == CanvasCategory.DataFlow:
        datasets = list(KnowledgebaseService.query(pipeline_id=canvas_id))
        c["datasets"] = [{"id": d.id, "name": d.name, "avatar": d.avatar} for d in datasets]

    return get_json_result(data=c)