def test_func_tool_annotated_arg() -> None:
    def my_function(my_arg: Annotated[str, "test description"]) -> str:
        return "result"

    tool = FunctionTool(my_function, description="Function tool.")
    assert tool.name == "my_function"
    assert tool.description == "Function tool."
    assert issubclass(tool.args_type(), BaseModel)
    assert issubclass(tool.return_type(), str)
    assert tool.args_type().model_fields["my_arg"].description == "test description"
    assert tool.args_type().model_fields["my_arg"].annotation is str
    assert tool.args_type().model_fields["my_arg"].is_required() is True
    assert tool.args_type().model_fields["my_arg"].default is PydanticUndefined
    assert len(tool.args_type().model_fields) == 1
    assert tool.return_type() is str
    assert tool.state_type() is None