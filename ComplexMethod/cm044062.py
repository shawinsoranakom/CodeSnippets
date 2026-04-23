async def test_get_apps_json_merges_templates_with_additional_sources(tmp_path):
    main = _load_main_with_mocks()
    apps_path = tmp_path / "workspace_apps.json"
    default_path = tmp_path / "default_apps.json"
    default_templates_data = json.dumps(
        [
            {"id": "from-default"},
            {"layout": [{"i": "widget-2"}]},
            {"tabs": {"tab1": {"layout": [{"i": "widget-3"}]}}},
        ]
    )
    apps_templates_data = json.dumps({"id": "default"})
    default_handle = mock_open(read_data=default_templates_data).return_value
    apps_handle = mock_open(read_data=apps_templates_data).return_value
    mocked_open = mock_open()
    mocked_open.side_effect = [default_handle, apps_handle]

    with (
        patch.object(main, "APPS_PATH", str(apps_path)),
        patch.object(main, "DEFAULT_APPS_PATH", str(default_path)),
        patch.object(
            main,
            "widgets_json",
            {
                "widget-2": {},
                "widget-3": {},
                "default": {},
                "from-default": {},
                "extra": {},
            },
        ),
        patch("openbb_platform_api.main.os.path.exists", return_value=True),
        patch.object(
            main,
            "get_widgets",
            AsyncMock(return_value={"default": {}, "from-default": {}, "extra": {}}),
        ),
        patch.object(
            main,
            "get_additional_apps",
            AsyncMock(
                return_value={"good": [{"id": "extra"}], "bad": {"id": "invalid"}}
            ),
        ),
        patch("openbb_platform_api.main.has_additional_apps", return_value=True),
        patch("openbb_platform_api.main.logger.error") as mock_log_error,
        patch("builtins.open", mocked_open),
    ):
        response = await main.get_apps_json()

    if mock_log_error.called:
        mock_log_error.assert_called_once()
    assert mocked_open.call_count == 2
    result = json.loads(response.body.decode())
    expected_core = [
        {"id": "default"},
        {"id": "from-default"},
        {"layout": [{"i": "widget-2"}]},
        {"tabs": {"tab1": {"layout": [{"i": "widget-3"}]}}},
    ]
    for item in expected_core:
        assert item in result
    if any(getattr(entry, "get", lambda *_: None)("id") == "extra" for entry in result):
        assert {"id": "extra"} in result