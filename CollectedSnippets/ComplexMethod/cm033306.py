async def list_pipeline_dataset_logs():
    kb_id = request.args.get("kb_id")
    if not kb_id:
        return get_json_result(data=False, message='Lack of "KB ID"', code=RetCode.ARGUMENT_ERROR)

    page_number = int(request.args.get("page", 0))
    items_per_page = int(request.args.get("page_size", 0))
    orderby = request.args.get("orderby", "create_time")
    if request.args.get("desc", "true").lower() == "false":
        desc = False
    else:
        desc = True
    create_date_from = request.args.get("create_date_from", "")
    create_date_to = request.args.get("create_date_to", "")
    if create_date_to > create_date_from:
        return get_data_error_result(message="Create data filter is abnormal.")

    req = await get_request_json()

    operation_status = req.get("operation_status", [])
    if operation_status:
        invalid_status = {s for s in operation_status if s not in VALID_TASK_STATUS}
        if invalid_status:
            return get_data_error_result(message=f"Invalid filter operation_status status conditions: {', '.join(invalid_status)}")

    try:
        logs, tol = PipelineOperationLogService.get_dataset_logs_by_kb_id(kb_id, page_number, items_per_page, orderby, desc, operation_status, create_date_from, create_date_to)
        return get_json_result(data={"total": tol, "logs": logs})
    except Exception as e:
        return server_error_response(e)