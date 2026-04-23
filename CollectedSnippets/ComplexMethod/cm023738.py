def attributes(self) -> dict[str, Any]:  # type: ignore[override]
        """State attributes."""
        if self._attributes is None:
            source = self._row.shared_attrs or self._row.attributes
            if self._attr_cache is not None and (
                attributes := self._attr_cache.get(source)
            ):
                self._attributes = attributes
                return attributes
            if source == EMPTY_JSON_OBJECT or source is None:
                self._attributes = {}
                return self._attributes
            try:
                self._attributes = json.loads(source)
            except ValueError:
                # When json.loads fails
                _LOGGER.exception(
                    "Error converting row to state attributes: %s", self._row
                )
                self._attributes = {}
            if self._attr_cache is not None:
                self._attr_cache[source] = self._attributes
        return self._attributes