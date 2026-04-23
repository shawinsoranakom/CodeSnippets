def determine_user_version():
    # Pre 0.2.0 directory
    old_dir_pre_020 = platformdirs.user_config_dir("Open Interpreter")
    # 0.2.0 directory
    old_dir_020 = platformdirs.user_config_dir("Open Interpreter Terminal")

    if os.path.exists(oi_dir) and os.listdir(oi_dir):
        # Check if the default.yaml profile exists and has a version key
        default_profile_path = os.path.join(oi_dir, "profiles", "default.yaml")
        if os.path.exists(default_profile_path):
            with open(default_profile_path, "r") as file:
                default_profile = yaml.safe_load(file)
                if "version" in default_profile:
                    return default_profile["version"]

    if os.path.exists(old_dir_020) or (
        os.path.exists(old_dir_pre_020) and os.path.exists(old_dir_020)
    ):
        # If both old_dir_pre_020 and old_dir_020 are found, or just old_dir_020, return 0.2.0
        return "0.2.0"
    if os.path.exists(old_dir_pre_020):
        # If only old_dir_pre_020 is found, return pre_0.2.0
        return "pre_0.2.0"
    # If none of the directories are found, return None
    return None