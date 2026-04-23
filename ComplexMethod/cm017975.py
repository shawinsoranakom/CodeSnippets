def teardown():
    """Clean up."""
    yield

    if os.path.isfile(YAML_PATH):
        os.remove(YAML_PATH)

    if os.path.isfile(SECRET_PATH):
        os.remove(SECRET_PATH)

    if os.path.isfile(VERSION_PATH):
        os.remove(VERSION_PATH)

    if os.path.isfile(AUTOMATIONS_PATH):
        os.remove(AUTOMATIONS_PATH)

    if os.path.isfile(SCRIPTS_PATH):
        os.remove(SCRIPTS_PATH)

    if os.path.isfile(SCENES_PATH):
        os.remove(SCENES_PATH)

    if os.path.isfile(SAFE_MODE_PATH):
        os.remove(SAFE_MODE_PATH)