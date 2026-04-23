def load(cls, path: str) -> None:
        """Load and parse a ``config.yaml`` file at *path*.

        Silently skips the file if PyYAML is not installed or the file does
        not exist.
        """
        if not has_yaml:
            debug.error("config.yaml: PyYAML is not installed – skipping config.yaml")
            return
        if not os.path.isfile(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except Exception as e:
            debug.error(f"config.yaml: Failed to parse {path}:", e)
            return

        if not isinstance(data, dict):
            debug.error(f"config.yaml: Expected a mapping at top level in {path}")
            return

        new_routes: Dict[str, ModelRouteConfig] = {}
        for entry in data.get("models", []):
            if not isinstance(entry, dict) or "name" not in entry:
                continue
            model_name = entry["name"]
            provider_list: List[ProviderRouteConfig] = []
            for pentry in entry.get("providers", []):
                if not isinstance(pentry, dict) or "provider" not in pentry:
                    continue
                provider_list.append(
                    ProviderRouteConfig(
                        provider=pentry["provider"],
                        model=pentry.get("model", model_name),
                        condition=pentry.get("condition"),
                    )
                )
            if provider_list:
                new_routes[model_name] = ModelRouteConfig(
                    name=model_name,
                    providers=provider_list,
                )

        cls.routes = new_routes
        debug.log(f"config.yaml: Loaded {len(new_routes)} model route(s) from {path}")