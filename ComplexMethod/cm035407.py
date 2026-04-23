def _extract_server_branch_last_modified(self, branch: dict) -> str | None:
        """Extract the last modified timestamp from a Bitbucket Server branch payload."""

        metadata = branch.get('metadata')
        if not isinstance(metadata, dict):
            return None

        for value in metadata.values():
            if not isinstance(value, list):
                continue
            for entry in value:
                if not isinstance(entry, dict):
                    continue
                timestamp = (
                    entry.get('authorTimestamp')
                    or entry.get('committerTimestamp')
                    or entry.get('timestamp')
                    or entry.get('lastModified')
                )
                if isinstance(timestamp, (int, float)):
                    return datetime.fromtimestamp(
                        timestamp / 1000, tz=timezone.utc
                    ).isoformat()
                if isinstance(timestamp, str):
                    # Some Bitbucket instances might already return ISO 8601 strings
                    return timestamp

        return None