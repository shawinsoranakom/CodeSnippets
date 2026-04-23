def test_config_load():
    # write example config to a file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(example_config)

    # load the config from the file
    config = Config.from_toml(f.name)

    assert config.paths.base == "./frontend"
    assert config.paths.src == "./src"
    assert config.run.build == "npm run build"
    assert config.run.test == "npm run test"
    assert config.run.lint == "quick-lint-js"
    assert config.gptengineer_app
    assert config.gptengineer_app.project_id == "..."
    assert config.gptengineer_app.openapi
    assert (
        config.gptengineer_app.openapi[0].url
        == "https://api.gptengineer.app/openapi.json"
    )
    assert (
        config.gptengineer_app.openapi[1].url
        == "https://some-color-translating-api/openapi.json"
    )
    assert config.to_dict()
    assert config.to_toml(f.name, save=False)

    # check that write+read is idempotent
    assert Config.from_toml(f.name) == config