def profile(interpreter, filename_or_url):
    # See if they're doing shorthand for a default profile
    filename_without_extension = os.path.splitext(filename_or_url)[0]
    for profile in default_profiles_names:
        if filename_without_extension == os.path.splitext(profile)[0]:
            filename_or_url = profile
            break

    profile_path = os.path.join(profile_dir, filename_or_url)
    profile = None

    # If they have a profile at a reserved profile name, rename it to {name}_custom.
    # Don't do this for the default one though.
    if (
        filename_or_url not in ["default", "default.yaml"]
        and filename_or_url in default_profiles_names
    ):
        if os.path.isfile(profile_path):
            base, extension = os.path.splitext(profile_path)
            os.rename(profile_path, f"{base}_custom{extension}")
        profile = get_default_profile(filename_or_url)

    if profile == None:
        try:
            profile = get_profile(filename_or_url, profile_path)
        except:
            if filename_or_url in ["default", "default.yaml"]:
                # Literally this just happens to default.yaml
                reset_profile(filename_or_url)
                profile = get_profile(filename_or_url, profile_path)
            else:
                raise

    return apply_profile(interpreter, profile, profile_path)