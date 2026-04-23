def fix_router_widgets(path, widgets):
    """Append the API prefix and path to the function, if necessary."""
    updated_widgets: dict = {}
    for widget_id, widget in widgets.items():
        if not isinstance(widget, dict) or widget_id.endswith("/widgets.json"):
            continue

        new_widget: dict = widget.copy()
        params = widget.get("params", [])

        if (endpoint := widget.get("endpoint", "")) and not endpoint.startswith(path):
            new_widget["endpoint"] = (
                path + endpoint[1:] if endpoint.startswith("/") else endpoint
            )

        if (
            (ws_endpoint := widget.get("wsEndpoint", ""))
            and "://" not in ws_endpoint
            and not ws_endpoint.startswith(path)
        ):
            new_widget["wsEndpoint"] = (
                path + ws_endpoint[1:] if ws_endpoint.startswith("/") else ws_endpoint
            )

        if (
            (img_url := widget.get("imgUrl", ""))
            and "://" not in img_url
            and not img_url.startswith(path)
        ):
            new_widget["imgUrl"] = (
                path + img_url[1:] if img_url.startswith("/") else img_url
            )

        new_params: list = []

        for param in params:
            new_param: dict = param.copy()

            if (
                (endpoint := param.get("endpoint", ""))
                and "://" not in endpoint
                and not endpoint.startswith(path)
            ):
                new_param["endpoint"] = (
                    path + endpoint[1:] if endpoint.startswith("/") else endpoint
                )

            if (
                (opt_endpoint := param.get("optionsEndpoint", ""))
                and "://" not in opt_endpoint
                and not opt_endpoint.startswith(path)
            ):
                new_param["optionsEndpoint"] = (
                    path + opt_endpoint[1:]
                    if opt_endpoint.startswith("/")
                    else opt_endpoint
                )

            new_params.append(new_param)

        new_widget["params"] = new_params
        updated_widgets[new_widget.get("widgetId", new_widget["endpoint"])] = new_widget

    return updated_widgets