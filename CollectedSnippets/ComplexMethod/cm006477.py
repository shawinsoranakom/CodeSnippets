async def read_folder_redirect(
    *,
    folder_id: UUID,
    params: Annotated[Params | None, Depends(custom_params)],
    is_component: bool = False,
    is_flow: bool = False,
    search: str = "",
):
    """Redirect to the projects endpoint."""
    redirect_url = f"/api/v1/projects/{folder_id}"
    params_list = []
    if is_component:
        params_list.append(f"is_component={is_component}")
    if is_flow:
        params_list.append(f"is_flow={is_flow}")
    if search:
        params_list.append(f"search={search}")
    if params and params.page:
        params_list.append(f"page={params.page}")
    if params and params.size:
        params_list.append(f"size={params.size}")

    if params_list:
        redirect_url += "?" + "&".join(params_list)

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)