def filter_loaded_components(self, data: dict, *, with_errors: bool) -> dict:
        from lfx.custom.utils import build_component

        items = []
        for menu in data["menu"]:
            components = []
            for component in menu["components"]:
                try:
                    if component["error"] if with_errors else not component["error"]:
                        component_tuple = (*build_component(component), component)
                        components.append(component_tuple)
                except Exception as exc:  # noqa: BLE001
                    logger.debug(
                        f"Skipping component {component['name']} from {component['file']} (load error)",
                        exc_info=exc,
                    )
                    continue
            items.append({"name": menu["name"], "path": menu["path"], "components": components})
        filtered = [menu for menu in items if menu["components"]]
        logger.debug(f"Filtered components {'with errors' if with_errors else ''}: {len(filtered)}")
        return {"menu": filtered}