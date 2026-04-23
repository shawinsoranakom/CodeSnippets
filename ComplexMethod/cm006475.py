async def read_project(
    *,
    session: DbSession,
    project_id: UUID,
    current_user: CurrentActiveUser,
    params: Annotated[Params | None, Depends(custom_params)],
    page: Annotated[int | None, Query()] = None,
    size: Annotated[int | None, Query()] = None,
    is_component: bool = False,
    is_flow: bool = False,
    search: str = "",
):
    try:
        project = (
            await session.exec(
                select(Folder)
                .options(selectinload(Folder.flows))
                .where(Folder.id == project_id, Folder.user_id == current_user.id)
            )
        ).first()
    except Exception as e:
        if "No result found" in str(e):
            raise HTTPException(status_code=404, detail="Project not found") from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Check if pagination is explicitly requested by the user (both page and size provided)
        if page is not None and size is not None:
            stmt = select(Flow).where(Flow.folder_id == project_id, Flow.user_id == current_user.id)

            if Flow.updated_at is not None:
                stmt = stmt.order_by(Flow.updated_at.desc())  # type: ignore[attr-defined]
            if is_component:
                stmt = stmt.where(Flow.is_component == True)  # noqa: E712
            if is_flow:
                stmt = stmt.where(Flow.is_component == False)  # noqa: E712
            if search:
                _search = _escape_like(search)
                stmt = stmt.where(Flow.name.like(f"%{_search}%", escape="\\"))  # type: ignore[attr-defined]

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", category=DeprecationWarning, module=r"fastapi_pagination\.ext\.sqlalchemy"
                )
                paginated_flows = await apaginate(session, stmt, params=params)

            return FolderWithPaginatedFlows(folder=FolderRead.model_validate(project), flows=paginated_flows)

        # If no pagination requested, return all flows for the current user
        flows_from_current_user_in_project = [flow for flow in project.flows if flow.user_id == current_user.id]
        project.flows = flows_from_current_user_in_project

        # Convert to FolderReadWithFlows while session is still active to avoid detached instance errors
        return FolderReadWithFlows.model_validate(project, from_attributes=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e