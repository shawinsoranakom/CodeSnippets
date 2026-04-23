def _parse_data(self) -> dict[str, list[NinaWarningData]]:
        """Parse warning data."""

        return_data: dict[str, list[NinaWarningData]] = {}

        for region_id, raw_warnings in self._remove_duplicate_warnings(
            self._nina.warnings
        ).items():
            warnings_for_regions: list[NinaWarningData] = []

            for raw_warn in raw_warnings:
                if re.search(
                    self.headline_filter, raw_warn.headline, flags=re.IGNORECASE
                ):
                    _LOGGER.debug(
                        f"Ignore warning ({raw_warn.id}) by headline filter ({self.headline_filter}) with headline: {raw_warn.headline}"
                    )
                    continue

                affected_areas_string: str = ", ".join(
                    [str(area) for area in raw_warn.affected_areas]
                )

                if not re.search(
                    self.area_filter, affected_areas_string, flags=re.IGNORECASE
                ):
                    _LOGGER.debug(
                        f"Ignore warning ({raw_warn.id}) by area filter ({self.area_filter}) with area: {affected_areas_string}"
                    )
                    continue

                shortened_affected_areas: str = (
                    affected_areas_string[0:250] + "..."
                    if len(affected_areas_string) > 250
                    else affected_areas_string
                )

                severity = (
                    None
                    if raw_warn.severity.lower() == "unknown"
                    else raw_warn.severity
                )

                warning_data: NinaWarningData = NinaWarningData(
                    raw_warn.id,
                    raw_warn.headline,
                    raw_warn.description,
                    raw_warn.sender or "",
                    severity,
                    " ".join([str(action) for action in raw_warn.recommended_actions]),
                    shortened_affected_areas,
                    affected_areas_string,
                    raw_warn.web or "",
                    datetime.fromisoformat(raw_warn.sent),
                    datetime.fromisoformat(raw_warn.start) if raw_warn.start else None,
                    datetime.fromisoformat(raw_warn.expires)
                    if raw_warn.expires
                    else None,
                    raw_warn.is_valid,
                )
                warnings_for_regions.append(warning_data)

            return_data[region_id] = warnings_for_regions

        return return_data