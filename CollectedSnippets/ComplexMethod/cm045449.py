def _apply_filter(self, messages: Sequence[BaseChatMessage]) -> Sequence[BaseChatMessage]:
        result: List[BaseChatMessage] = []

        for source_filter in self._filter.per_source:
            msgs = [m for m in messages if m.source == source_filter.source]

            if source_filter.position == "first" and source_filter.count:
                msgs = msgs[: source_filter.count]
            elif source_filter.position == "last" and source_filter.count:
                msgs = msgs[-source_filter.count :]

            result.extend(msgs)

        return result