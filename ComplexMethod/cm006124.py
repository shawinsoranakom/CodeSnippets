async def test_download_project_sanitizes_windows_path_characters(
    client: AsyncClient, logged_in_headers, basic_case, active_user
):
    create_response = await client.post("api/v1/projects/", json=basic_case, headers=logged_in_headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    project_id = create_response.json()["id"]

    async with session_scope() as session:
        flow_create = FlowCreate(
            name=r"..\evil\flow",
            description="Flow with unsafe filename characters",
            data={"nodes": [], "edges": []},
            folder_id=project_id,
            user_id=active_user.id,
        )
        flow = Flow.model_validate(flow_create.model_dump(exclude={"id"}))
        session.add(flow)
        await session.flush()
        await session.refresh(flow)
        await session.commit()

    response = await client.get(f"api/v1/projects/download/{project_id}", headers=logged_in_headers)
    assert response.status_code == status.HTTP_200_OK

    with zipfile.ZipFile(io.BytesIO(response.content), "r") as zip_file:
        file_names = zip_file.namelist()
        assert len(file_names) == 1
        assert "/" not in file_names[0]
        assert "\\" not in file_names[0]
        assert ".." not in file_names[0]
        assert file_names[0].endswith(".json")