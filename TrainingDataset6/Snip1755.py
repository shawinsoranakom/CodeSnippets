def _build_response_args(
    *, status_code: int | None, solved_result: Any
) -> dict[str, Any]:
    response_args: dict[str, Any] = {
        "background": solved_result.background_tasks,
    }
    # If status_code was set, use it, otherwise use the default from the
    # response class, in the case of redirect it's 307
    current_status_code = (
        status_code if status_code else solved_result.response.status_code
    )
    if current_status_code is not None:
        response_args["status_code"] = current_status_code
    if solved_result.response.status_code:
        response_args["status_code"] = solved_result.response.status_code
    return response_args