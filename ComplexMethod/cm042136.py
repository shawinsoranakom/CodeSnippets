async def test_write_prd_api(context):
    action = WritePRD()
    result = await action.run(user_requirement="write a snake game.")
    assert isinstance(result, str)
    assert result
    assert str(DEFAULT_WORKSPACE_ROOT) in result

    result = await action.run(
        user_requirement="write a snake game.",
        output_pathname=str(Path(context.config.project_path) / f"{uuid.uuid4().hex}.json"),
    )
    assert isinstance(result, str)
    assert result
    assert str(context.config.project_path) in result

    ix = result.find(":")
    legacy_prd_filename = result[ix + 1 :].replace('"', "").strip()

    result = await action.run(user_requirement="Add moving enemy.", legacy_prd_filename=legacy_prd_filename)
    assert isinstance(result, str)
    assert result
    assert str(DEFAULT_WORKSPACE_ROOT) in result

    result = await action.run(
        user_requirement="Add moving enemy.",
        output_pathname=str(Path(context.config.project_path) / f"{uuid.uuid4().hex}.json"),
        legacy_prd_filename=legacy_prd_filename,
    )
    assert isinstance(result, str)
    assert result
    assert str(context.config.project_path) in result