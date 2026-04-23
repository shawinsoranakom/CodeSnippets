async def test_create_and_read_project_cyrillic(client: AsyncClient, logged_in_headers):
    """Ensure that the API correctly handles non-ASCII (Cyrillic) characters during project creation and retrieval."""
    payload = {
        "name": CYRILLIC_NAME,
        "description": CYRILLIC_DESC,
        "flows_list": [],
        "components_list": [],
    }

    # Create the project with Cyrillic characters
    create_resp = await client.post("api/v1/projects/", json=payload, headers=logged_in_headers)
    assert create_resp.status_code == status.HTTP_201_CREATED
    created = create_resp.json()
    assert created["name"] == CYRILLIC_NAME
    assert created["description"] == CYRILLIC_DESC
    proj_id = created["id"]

    # Fetch the project back to verify round-trip UTF-8 integrity
    get_resp = await client.get(f"api/v1/projects/{proj_id}", headers=logged_in_headers)
    assert get_resp.status_code == status.HTTP_200_OK
    fetched = get_resp.json()

    # Handle potential pagination/envelope variations already seen in other tests
    if isinstance(fetched, dict) and "folder" in fetched:
        fetched = fetched["folder"]
    elif isinstance(fetched, dict) and "project" in fetched:
        fetched = fetched["project"]

    assert fetched["name"] == CYRILLIC_NAME
    assert fetched["description"] == CYRILLIC_DESC