def check_dummies(overwrite: bool = False):
    """
    Check if the dummy files are up to date and maybe `overwrite` with the right content.

    Args:
        overwrite (`bool`, *optional*, default to `False`):
            Whether or not to overwrite the content of the dummy files. Will raise an error if they are not up to date
            when `overwrite=False`.
    """
    dummy_files = create_dummy_files()
    # For special correspondence backend name to shortcut as used in utils/dummy_xxx_objects.py
    short_names = {"torch": "pt"}

    # Locate actual dummy modules and read their content.
    path = os.path.join(PATH_TO_TRANSFORMERS, "utils")
    dummy_file_paths = {
        backend: os.path.join(path, f"dummy_{short_names.get(backend, backend)}_objects.py") for backend in dummy_files
    }

    actual_dummies = {}
    for backend, file_path in dummy_file_paths.items():
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8", newline="\n") as f:
                actual_dummies[backend] = f.read()
        else:
            actual_dummies[backend] = ""

    # Compare actual with what they should be.
    for backend in dummy_files:
        if dummy_files[backend] != actual_dummies[backend]:
            if overwrite:
                print(
                    f"Updating transformers.utils.dummy_{short_names.get(backend, backend)}_objects.py as the main "
                    "__init__ has new objects."
                )
                with open(dummy_file_paths[backend], "w", encoding="utf-8", newline="\n") as f:
                    f.write(dummy_files[backend])
            else:
                # Temporary fix to help people identify which objects introduced are not correctly protected.
                found = False
                for _actual, _dummy in zip(
                    actual_dummies["torch"].split("class"), dummy_files["torch"].split("class")
                ):
                    if _actual != _dummy:
                        actual_broken = _actual
                        dummy_broken = _dummy
                        found = True
                        break

                if not found:
                    print("A transient error was found with the dummies, please investigate.")
                    continue

                raise ValueError(
                    "The main __init__ has objects that are not present in "
                    f"transformers.utils.dummy_{short_names.get(backend, backend)}_objects.py.\n"
                    f" It is likely the following objects are responsible, see these excerpts: \n"
                    f"---------------------------------- Actual -------------------------------------\n"
                    f" \n {actual_broken} \n"
                    f"---------------------------------- Dummy -------------------------------------\n"
                    f" \n {dummy_broken} \n"
                    "Run `make fix-repo` to fix this."
                )