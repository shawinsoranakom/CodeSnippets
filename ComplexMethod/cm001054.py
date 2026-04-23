async def test_list_folders_tree_with_agents_includes_root(list_tool, session):
    tree = [_make_tree(id="r1", name="Root")]
    raw_map = {"r1": [{"id": "a1", "name": "Foldered", "description": "In folder"}]}
    root_raw = [{"id": "a2", "name": "Loose Agent", "description": "At root"}]
    with patch("backend.copilot.tools.manage_folders.library_db") as mock_lib:
        mock_lib.return_value.get_folder_tree = AsyncMock(return_value=tree)
        mock_lib.return_value.get_folder_agents_map = AsyncMock(return_value=raw_map)
        mock_lib.return_value.get_root_agent_summaries = AsyncMock(
            return_value=root_raw
        )
        result = await list_tool._execute(
            user_id=_TEST_USER_ID, session=session, include_agents=True
        )

    assert isinstance(result, FolderListResponse)
    assert result.root_agents is not None
    assert len(result.root_agents) == 1
    assert result.root_agents[0].name == "Loose Agent"
    assert result.tree is not None
    assert result.tree[0].agents is not None
    assert result.tree[0].agents[0].name == "Foldered"
    mock_lib.return_value.get_root_agent_summaries.assert_awaited_once_with(
        _TEST_USER_ID
    )