def get_widgets_json(
    _build: bool,
    _openapi,
    widget_exclude_filter: list,
    editable: bool = False,
    widgets_path: str | None = None,
    app: FastAPI | None = None,
):
    """Generate and serve the widgets.json for the OpenBB Platform API."""
    # pylint: disable=import-outside-toplevel
    from openbb_core.provider.utils.helpers import run_async  # noqa
    from .merge_widgets import get_and_fix_widget_paths, has_additional_widgets
    from .widgets import build_json

    global PATH_WIDGETS  # noqa  pylint: disable=W0603

    if (
        FIRST_RUN is True
        and app
        and isinstance(app, FastAPI)
        and has_additional_widgets(app)
    ):
        PATH_WIDGETS = run_async(get_and_fix_widget_paths, app)

    if PATH_WIDGETS and (
        to_exclude := [p + "*" for p in PATH_WIDGETS if p.endswith("/")]
    ):
        # Exclude explicit router paths from the automated generation.
        # These widgets have been added by a router, so we assume they don't want
        # the factory for those paths.
        widget_exclude_filter.extend(to_exclude)

    if editable is True:
        if widgets_path is None:
            python_path = Path(sys.executable)
            parent_path = (
                python_path.parent if os.name == "nt" else python_path.parents[1]
            )
            widgets_json_path = parent_path.joinpath("assets", "widgets.json").resolve()
        else:
            widgets_json_path = Path(widgets_path).absolute().resolve()

        json_exists = widgets_json_path.exists()

        if not json_exists:
            widgets_json_path.parent.mkdir(parents=True, exist_ok=True)
            _build = True
            json_exists = widgets_json_path.exists()

        existing_widgets_json: dict = {}

        if json_exists:
            with open(widgets_json_path, encoding="utf-8") as f:
                existing_widgets_json = json.load(f)

        _widgets_json = (
            existing_widgets_json
            if _build is False
            else build_json(_openapi, widget_exclude_filter)
        )

        if _build:
            diff = DeepDiff(existing_widgets_json, _widgets_json, ignore_order=True)
            merge_prompt = None
            if diff and json_exists:
                print("Differences found:", diff)  # noqa: T201
                merge_prompt = input(
                    "\nDo you want to overwrite the existing widgets.json configuration?"
                    "\nEnter 'n' to append existing with only new entries, or 'i' to ignore all changes. (y/n/i): "
                )
                if merge_prompt.lower().startswith("n"):
                    _widgets_json.update(existing_widgets_json)
                elif merge_prompt.lower().startswith("i"):
                    _widgets_json = existing_widgets_json

            if merge_prompt is None or not merge_prompt.lower().startswith("i"):
                try:
                    with open(widgets_json_path, "w", encoding="utf-8") as f:
                        json.dump(_widgets_json, f, ensure_ascii=False, indent=4)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(  # noqa
                        f"Error writing widgets.json: {e}.  Loading from memory instead."
                    )
                    _widgets_json = (
                        existing_widgets_json
                        if existing_widgets_json
                        else build_json(_openapi, widget_exclude_filter)
                    )
    else:
        _widgets_json = build_json(_openapi, widget_exclude_filter)

        if PATH_WIDGETS:
            for k in PATH_WIDGETS:
                if k in widget_exclude_filter or k + "*" in widget_exclude_filter:
                    continue

                for widget_id, widget in PATH_WIDGETS[k].items():
                    if widget_id not in widget_exclude_filter:
                        _widgets_json[widget_id] = widget

    return _widgets_json