def _to_plain_dict(self, obj: Any) -> Any:
        """Recursively convert SDK models/lists to plain Python dicts/lists for safe .get access."""
        try:
            if isinstance(obj, dict):
                return {k: self._to_plain_dict(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple, set)):
                return [self._to_plain_dict(v) for v in obj]
            if hasattr(obj, "model_dump"):
                try:
                    return self._to_plain_dict(obj.model_dump())
                except (TypeError, AttributeError, ValueError):
                    pass
            if hasattr(obj, "__dict__") and not isinstance(obj, (str, bytes)):
                try:
                    return self._to_plain_dict({k: v for k, v in obj.__dict__.items() if not k.startswith("_")})
                except (TypeError, AttributeError, ValueError):
                    pass
        except (TypeError, ValueError, AttributeError, RecursionError):
            return obj
        else:
            return obj