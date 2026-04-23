def reset_profile(specific_default_profile=None):
    if (
        specific_default_profile
        and specific_default_profile not in default_profiles_names
    ):
        raise ValueError(
            f"The specific default profile '{specific_default_profile}' is not a default profile."
        )

    # Check version, before making the profile directory
    current_version = determine_user_version()

    for default_yaml_file in default_profiles_paths:
        filename = os.path.basename(default_yaml_file)

        if specific_default_profile and filename != specific_default_profile:
            continue

        # Only reset default.yaml, all else are loaded from python package
        if specific_default_profile != "default.yaml":
            continue

        target_file = os.path.join(profile_dir, filename)

        # Variable to see if we should display the 'reset' print statement or not
        create_oi_directory = False

        # Make the profile directory if it does not exist
        if not os.path.exists(profile_dir):
            if not os.path.exists(oi_dir):
                create_oi_directory = True

            os.makedirs(profile_dir)

        if not os.path.exists(target_file):
            shutil.copy(default_yaml_file, target_file)
            if current_version is None:
                # If there is no version, add it to the default yaml
                with open(target_file, "a") as file:
                    file.write(
                        f"\nversion: {OI_VERSION}  # Profile version (do not modify)"
                    )
            if not create_oi_directory:
                print(f"{filename} has been reset.")
        else:
            with open(target_file, "r") as file:
                current_profile = file.read()
            if current_profile not in historical_profiles:
                user_input = input(f"Would you like to reset/update {filename}? (y/n) ")
                if user_input.lower() == "y":
                    send2trash.send2trash(
                        target_file
                    )  # This way, people can recover it from the trash
                    shutil.copy(default_yaml_file, target_file)
                    print(f"{filename} has been reset.")
                else:
                    print(f"{filename} was not reset.")
            else:
                shutil.copy(default_yaml_file, target_file)
                print(f"{filename} has been reset.")