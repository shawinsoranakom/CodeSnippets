async def test_event_data(address, payload, value=None):
        assert len(events) == 1
        event = events.pop()
        assert event.data["data"] == payload
        assert event.data["value"] == value
        assert event.data["direction"] == "Incoming"
        assert event.data["destination"] == address
        if payload is None:
            assert event.data["telegramtype"] == "GroupValueRead"
        else:
            assert event.data["telegramtype"] in (
                "GroupValueWrite",
                "GroupValueResponse",
            )
        assert event.data["source"] == KNXTestKit.INDIVIDUAL_ADDRESS