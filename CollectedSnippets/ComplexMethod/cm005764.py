async def check_messages(flow_id):
    if isinstance(flow_id, str):
        flow_id = UUID(flow_id)
    messages = await aget_messages(flow_id=flow_id, order="ASC")
    flow_id_str = str(flow_id)
    assert len(messages) == 2
    assert messages[0].session_id == flow_id_str
    assert messages[0].sender == "User"
    assert messages[0].sender_name == "User"
    assert messages[0].text == ""
    assert messages[1].session_id == flow_id_str
    assert messages[1].sender == "Machine"
    assert messages[1].sender_name == "AI"