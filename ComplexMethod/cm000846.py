def load_previous(self, content: str, log_prefix: str = "[Transcript]") -> None:
        """Load complete previous transcript.

        This loads the FULL previous context. As new messages come in,
        we append to this state. The final output is the complete context
        (previous + new), not just the delta.
        """
        if not content or not content.strip():
            return

        lines = content.strip().split("\n")
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue

            data = json.loads(line, fallback=None)
            if data is None:
                logger.warning(
                    "%s Failed to parse transcript line %d/%d",
                    log_prefix,
                    line_num,
                    len(lines),
                )
                continue

            entry = self._parse_entry(data)
            if entry is None:
                continue
            self._entries.append(entry)
            self._last_uuid = entry.uuid

        logger.info(
            "%s Loaded %d entries from previous transcript (last_uuid=%s)",
            log_prefix,
            len(self._entries),
            self._last_uuid[:12] if self._last_uuid else None,
        )