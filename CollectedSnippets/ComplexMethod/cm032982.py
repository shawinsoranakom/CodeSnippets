def _resolve_entry_time(self, entry: Any) -> datetime:
        for field in ("updated_parsed", "published_parsed"):
            value = entry.get(field)
            if value:
                return self._struct_time_to_utc(value)

        for field in ("updated", "published"):
            value = entry.get(field)
            if isinstance(value, str) and value.strip():
                try:
                    parsed = parsedate_to_datetime(value)
                except (TypeError, ValueError, IndexError):
                    continue
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)

        return datetime.now(timezone.utc)