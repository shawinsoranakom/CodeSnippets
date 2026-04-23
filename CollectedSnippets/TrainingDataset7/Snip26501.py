def stored_session_messages_count(storage):
    data = storage.deserialize_messages(
        storage.request.session.get(storage.session_key, [])
    )
    return len(data)