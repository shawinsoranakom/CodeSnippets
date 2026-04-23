def _resolve_ns_prefix(ns_uri: str, ns_prefix_map: dict[str, str]) -> str:
        """Resolve a namespace URI to its prefix.

        Uses the document's xmlns declarations first, then falls back
        to well-known patterns, and finally extracts the semantic
        segment from the URI path.

        Parameters
        ----------
        ns_uri : str
            The full namespace URI (without braces).
        ns_prefix_map : dict[str, str]
            Mapping of namespace URI → prefix from xmlns declarations.

        Returns
        -------
        str
            The resolved prefix string.
        """
        # 1. Direct lookup from xmlns declarations
        if ns_uri in ns_prefix_map:
            return ns_prefix_map[ns_uri]

        # 2. Well-known patterns
        if "us-gaap" in ns_uri:
            return "us-gaap"
        if "xbrl.sec.gov/dei" in ns_uri:
            return "dei"
        if "fasb.org/srt" in ns_uri:
            return "srt"

        # 3. Heuristic: for URIs like http://xbrl.sec.gov/ecd/2024,
        #    take the segment before the trailing year/date
        import re  # pylint: disable=import-outside-toplevel

        parts = ns_uri.rstrip("/").split("/")
        # Walk backwards past date-like segments to find the semantic name.
        # Matches: 2024, 2024-01, 2024-01-15, 20240928
        for part in reversed(parts):
            if not re.match(r"^\d{4}(-?\d{2}(-?\d{2})?)?$", part):
                return part

        return parts[-1] if parts else "unknown"