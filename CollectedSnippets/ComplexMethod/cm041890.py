def migrate_app_directory(old_dir, new_dir, profile_dir):
    # Copy the "profiles" folder and its contents if it exists
    profiles_old_path = os.path.join(old_dir, "profiles")
    profiles_new_path = os.path.join(new_dir, "profiles")
    if os.path.exists(profiles_old_path):
        os.makedirs(profiles_new_path, exist_ok=True)
        # Iterate over all files in the old profiles directory
        for filename in os.listdir(profiles_old_path):
            old_file_path = os.path.join(profiles_old_path, filename)
            new_file_path = os.path.join(profiles_new_path, filename)

            # Migrate yaml files to new format
            if filename.endswith(".yaml"):
                migrate_profile(old_file_path, new_file_path)
            else:
                # if not yaml, just copy it over
                shutil.copy(old_file_path, new_file_path)

    # Copy the "conversations" folder and its contents if it exists
    conversations_old_path = os.path.join(old_dir, "conversations")
    conversations_new_path = os.path.join(new_dir, "conversations")
    if os.path.exists(conversations_old_path):
        shutil.copytree(
            conversations_old_path, conversations_new_path, dirs_exist_ok=True
        )

    # Migrate the "config.yaml" file to the new format
    config_old_path = os.path.join(old_dir, "config.yaml")
    if os.path.exists(config_old_path):
        new_file_path = os.path.join(profiles_new_path, "default.yaml")
        migrate_profile(config_old_path, new_file_path)

    # After all migrations have taken place, every yaml file should have a version listed. Sometimes, if the user does not have a default.yaml file from 0.2.0, it will not add the version to the file, causing the migration message to show every time interpreter is launched. This code loops through all yaml files post migration, and ensures they have a version number, to prevent the migration message from showing.
    for filename in os.listdir(profiles_new_path):
        if filename.endswith(".yaml"):
            file_path = os.path.join(profiles_new_path, filename)
            with open(file_path, "r") as file:
                lines = file.readlines()

            # Check if a version line already exists
            version_exists = any(line.strip().startswith("version:") for line in lines)

            if not version_exists:
                with open(file_path, "a") as file:  # Open for appending
                    file.write("\nversion: 0.2.1  # Profile version (do not modify)")