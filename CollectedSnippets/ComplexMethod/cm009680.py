def test_add_message_implementation_only() -> None:
    """Test implementation of add_message only."""

    class SampleChatHistory(BaseChatMessageHistory):
        def __init__(self, *, store: list[BaseMessage]) -> None:
            self.store = store

        def add_message(self, message: BaseMessage) -> None:
            """Add a message to the store."""
            self.store.append(message)

        def clear(self) -> None:
            """Clear the store."""
            raise NotImplementedError

    store: list[BaseMessage] = []
    chat_history = SampleChatHistory(store=store)
    chat_history.add_message(HumanMessage(content="Hello"))
    assert len(store) == 1
    assert store[0] == HumanMessage(content="Hello")
    chat_history.add_message(HumanMessage(content="World"))
    assert len(store) == 2
    assert store[1] == HumanMessage(content="World")

    chat_history.add_messages(
        [
            HumanMessage(content="Hello"),
            HumanMessage(content="World"),
        ]
    )
    assert len(store) == 4
    assert store[2] == HumanMessage(content="Hello")
    assert store[3] == HumanMessage(content="World")