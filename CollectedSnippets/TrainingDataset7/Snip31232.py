def get_label_module(label):
    """Return the top-level module part for a test label."""
    path = Path(label)
    if len(path.parts) == 1:
        # Interpret the label as a dotted module name.
        return label.split(".")[0]

    # Otherwise, interpret the label as a path. Check existence first to
    # provide a better error message than relative_to() if it doesn't exist.
    if not path.exists():
        raise RuntimeError(f"Test label path {label} does not exist")
    path = path.resolve()
    rel_path = path.relative_to(RUNTESTS_DIR)
    return rel_path.parts[0]