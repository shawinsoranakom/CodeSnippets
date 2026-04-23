async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send notification to specified EventBus."""

        cleaned_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        data = cleaned_kwargs.get(ATTR_DATA, {})
        detail = (
            json.dumps(data["detail"])
            if "detail" in data
            else json.dumps({"message": message})
        )

        async with self.session.create_client(
            self.service, **self.aws_config
        ) as client:
            entries = []
            for target in kwargs.get(ATTR_TARGET, [None]):
                entry = {
                    "Source": data.get("source", "homeassistant"),
                    "Resources": data.get("resources", []),
                    "Detail": detail,
                    "DetailType": data.get("detail_type", ""),
                }
                if target:
                    entry["EventBusName"] = target

                entries.append(entry)
            tasks = [
                client.put_events(Entries=entries[i : min(i + 10, len(entries))])
                for i in range(0, len(entries), 10)
            ]

            if tasks:
                results = await asyncio.gather(*tasks)
                for result in results:
                    for entry in result["Entries"]:
                        if len(entry.get("EventId", "")) == 0:
                            _LOGGER.error(
                                "Failed to send event: ErrorCode=%s ErrorMessage=%s",
                                entry["ErrorCode"],
                                entry["ErrorMessage"],
                            )