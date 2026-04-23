def _merge_serialized_report(report: SnapshotReport, json_data: dict[str, Any]) -> None:
    _merge_serialized_collections(report.discovered, json_data["discovered"])
    _merge_serialized_collections(report.created, json_data["created"])
    _merge_serialized_collections(report.failed, json_data["failed"])
    _merge_serialized_collections(report.matched, json_data["matched"])
    _merge_serialized_collections(report.updated, json_data["updated"])
    _merge_serialized_collections(report.used, json_data["used"])
    for collected_item in json_data["_collected_items"]:
        custom_item = _FakePytestItem(collected_item)
        if not any(
            t.nodeid == custom_item.nodeid and t.name == custom_item.nodeid
            for t in report.collected_items
        ):
            report.collected_items.add(custom_item)
    for key, selected_item in json_data["_selected_items"].items():
        if key in report.selected_items:
            status = ItemStatus(selected_item)
            if status != ItemStatus.NOT_RUN:
                report.selected_items[key] = status
        else:
            report.selected_items[key] = ItemStatus(selected_item)