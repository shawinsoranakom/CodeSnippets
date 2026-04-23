def find_extensions(filter_chart: bool | None = True):
    """Find extensions."""
    filter_ext = ["tests", "__pycache__"]
    if filter_chart:
        filter_ext.append("charting")
    extensions = [x for x in (ROOT_DIR / "extensions").iterdir() if x.is_dir()]
    extensions.extend(
        [x for x in (ROOT_DIR / "obbject_extensions").iterdir() if x.is_dir()]
    )
    extensions.extend([x for x in (ROOT_DIR / "providers").iterdir() if x.is_dir()])
    extensions = [x for x in extensions if x.name not in filter_ext]
    return extensions