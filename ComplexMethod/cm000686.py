async def test_table_input_with_data():
    """Test AgentTableInputBlock with actual table data."""
    block = AgentTableInputBlock()

    input_data = block.Input(
        name="test_table",
        column_headers=["Name", "Age", "City"],
        value=[
            {"Name": "John", "Age": "30", "City": "New York"},
            {"Name": "Jane", "Age": "25", "City": "London"},
            {"Name": "Bob", "Age": "35", "City": "Paris"},
        ],
    )

    output_data = []
    async for output_name, output_value in block.run(input_data):
        output_data.append((output_name, output_value))

    assert len(output_data) == 1
    assert output_data[0][0] == "result"

    result = output_data[0][1]
    assert len(result) == 3
    assert result[0]["Name"] == "John"
    assert result[1]["Age"] == "25"
    assert result[2]["City"] == "Paris"