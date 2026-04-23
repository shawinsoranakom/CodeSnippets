async def test_write_directory_serdeser(language: str, topic: str, context):
    action = WriteDirectory(context=context)
    serialized_data = action.model_dump()
    assert serialized_data["name"] == "WriteDirectory"
    assert serialized_data["language"] == "Chinese"

    new_action = WriteDirectory(**serialized_data, context=context)
    ret = await new_action.run(topic=topic)
    assert isinstance(ret, dict)
    assert "title" in ret
    assert "directory" in ret
    assert isinstance(ret["directory"], list)
    assert len(ret["directory"])
    assert isinstance(ret["directory"][0], dict)