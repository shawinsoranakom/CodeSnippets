def refresh(self) -> None:
        """Re-scan the workspace and reload all ``.pa.py`` providers."""
        entries: List[tuple] = []
        for pa_path in list_pa_providers():
            try:
                cls = load_pa_provider(pa_path)
                if cls is None:
                    continue
                provider_id = self._make_id(pa_path)
                models_list: List[str] = []
                try:
                    if hasattr(cls, "get_models"):
                        raw = cls.get_models()
                        models_list = list(raw) if raw else []
                    elif hasattr(cls, "models"):
                        models_list = list(getattr(cls, "models") or [])
                except Exception:
                    pass
                entries.append((
                    provider_id,
                    getattr(cls, "label", cls.__name__),
                    models_list,
                    bool(getattr(cls, "working", True)),
                    getattr(cls, "url", None),
                    cls,
                ))
            except Exception:
                pass
        self._entries = entries
        self._loaded_at = _time_module.monotonic()