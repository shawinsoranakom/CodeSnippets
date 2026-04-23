def test_base_path_changes(set_base_dir):
    test_dir = os.path.abspath("/test/dir")
    set_base_dir(test_dir)

    assert folder_paths.base_path == test_dir
    assert folder_paths.models_dir == os.path.join(test_dir, "models")
    assert folder_paths.input_directory == os.path.join(test_dir, "input")
    assert folder_paths.output_directory == os.path.join(test_dir, "output")
    assert folder_paths.temp_directory == os.path.join(test_dir, "temp")
    assert folder_paths.user_directory == os.path.join(test_dir, "user")

    assert os.path.join(test_dir, "custom_nodes") in folder_paths.get_folder_paths("custom_nodes")

    for name in ["checkpoints", "loras", "vae", "configs", "embeddings", "controlnet", "classifiers"]:
        assert folder_paths.get_folder_paths(name)[0] == os.path.join(test_dir, "models", name)