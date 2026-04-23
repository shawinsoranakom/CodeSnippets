def update_version_in_examples(version: str, patch: bool = False):
    """
    Update the version in all examples files.

    Args:
        version (`str`): The new version to set in the examples.
        patch (`bool`, *optional*, defaults to `False`): Whether or not this is a patch release.
    """
    for folder, directories, fnames in os.walk(PATH_TO_EXAMPLES):
        # Removing some of the folders with non-actively maintained examples from the walk
        if "legacy" in directories:
            directories.remove("legacy")
        for fname in fnames:
            if fname.endswith(".py"):
                if UV_SCRIPT_MARKER in Path(folder, fname).read_text():
                    # Update the dependencies in UV scripts
                    uv_script_file_type = "uv_script_dev" if ".dev" in version else "uv_script_release"
                    update_version_in_file(os.path.join(folder, fname), version, file_type=uv_script_file_type)
                if not patch:
                    # We don't update the version in the examples for patch releases.
                    update_version_in_file(os.path.join(folder, fname), version, file_type="examples")