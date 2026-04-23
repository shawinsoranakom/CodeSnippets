def test_fix_router_widgets_updates_nested_paths_without_mutating_source():
    original = {
        "widgetA": {
            "widgetId": "widgetA",
            "endpoint": "/data",
            "wsEndpoint": "/stream",
            "imgUrl": "/images/icon.png",
            "params": [
                {
                    "name": "param1",
                    "endpoint": "/param",
                    "optionsEndpoint": "/param/options",
                },
                {"name": "param2", "endpoint": "http://external/api"},
            ],
        },
        "widgetB/widgets.json": {"endpoint": "/should/skip"},
        "not_a_dict": "skip_me",
    }
    snapshot = copy.deepcopy(original)
    updated = fix_router_widgets("/api/", original)

    assert snapshot == original
    assert list(updated.keys()) == ["widgetA"]
    widget = updated["widgetA"]
    assert widget["endpoint"] == "/api/data"
    assert widget["wsEndpoint"] == "/api/stream"
    assert widget["imgUrl"] == "/api/images/icon.png"
    assert widget["params"][0]["endpoint"] == "/api/param"
    assert widget["params"][0]["optionsEndpoint"] == "/api/param/options"
    assert widget["params"][1]["endpoint"] == "http://external/api"