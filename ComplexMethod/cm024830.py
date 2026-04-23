async def test_loading_corrupt_core_file(
    tmpdir: py.path.local, caplog: pytest.LogCaptureFixture
) -> None:
    """Test we handle unrecoverable corruption in a core file."""
    loop = asyncio.get_running_loop()
    tmp_storage = await loop.run_in_executor(None, tmpdir.mkdir, "temp_storage")

    async with async_test_home_assistant(config_dir=tmp_storage.strpath) as hass:
        storage_key = "core.anything"
        store = storage.Store(
            hass, MOCK_VERSION_2, storage_key, minor_version=MOCK_MINOR_VERSION_1
        )
        await store.async_save({"hello": "world"})
        storage_path = os.path.join(tmp_storage, ".storage")
        store_file = os.path.join(storage_path, store.key)

        data = await store.async_load()
        assert data == {"hello": "world"}

        def _corrupt_store():
            with open(store_file, "w", encoding="utf8") as f:
                f.write("corrupt")

        await hass.async_add_executor_job(_corrupt_store)

        data = await store.async_load()
        assert data is None
        assert "Unrecoverable error decoding storage" in caplog.text

        issue_registry = ir.async_get(hass)
        found_issue = None
        issue_entry = None
        for (domain, issue), entry in issue_registry.issues.items():
            if domain == HOMEASSISTANT_DOMAIN and issue.startswith(
                f"storage_corruption_{storage_key}_"
            ):
                found_issue = issue
                issue_entry = entry
                break

        assert found_issue is not None
        assert issue_entry is not None
        assert issue_entry.is_fixable is True
        assert issue_entry.translation_placeholders["storage_key"] == storage_key
        assert issue_entry.issue_domain == HOMEASSISTANT_DOMAIN
        assert (
            "unexpected character: line 1 column 1 (char 0)"
            in issue_entry.translation_placeholders["error"]
        )

        files = await hass.async_add_executor_job(
            os.listdir, os.path.join(tmp_storage, ".storage")
        )
        assert ".corrupt" in files[0]

        await hass.async_stop(force=True)