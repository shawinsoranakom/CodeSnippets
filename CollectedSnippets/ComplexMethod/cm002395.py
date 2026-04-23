def sort_all_auto_mappings(overwrite: bool = False):
    """
    Sort all auto mappings in the library.

    Args:
        overwrite (`bool`, *optional*, defaults to `False`): Whether or not to fix and overwrite the file.
    """
    fnames = [os.path.join(PATH_TO_AUTO_MODULE, f) for f in os.listdir(PATH_TO_AUTO_MODULE) if f.endswith(".py")]
    diffs = [sort_auto_mapping(fname, overwrite=overwrite) for fname in fnames]

    if not overwrite and any(diffs):
        failures = [f for f, d in zip(fnames, diffs) if d]
        raise ValueError(
            f"The following files have auto mappings that need sorting: {', '.join(failures)}. Run `make style` to fix"
            " this."
        )