def test_csv_input() -> None:
    """Test CSV file input with both LangChain standard and OpenAI native formats."""
    # Create sample CSV content
    csv_content = (
        "name,age,city\nAlice,30,New York\nBob,25,Los Angeles\nCarol,35,Chicago"
    )
    csv_bytes = csv_content.encode("utf-8")
    base64_string = base64.b64encode(csv_bytes).decode("utf-8")

    llm = ChatOpenAI(model=MODEL_NAME, use_responses_api=True)

    # Test LangChain standard format
    langchain_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "How many people are in this CSV file?",
            },
            {
                "type": "file",
                "base64": base64_string,
                "mime_type": "text/csv",
                "filename": "people.csv",
            },
        ],
    }
    payload = llm._get_request_payload([langchain_message])
    block = payload["input"][0]["content"][1]
    assert block["type"] == "input_file"

    response = llm.invoke([langchain_message])
    assert isinstance(response, AIMessage)
    assert response.content
    assert (
        "3" in str(response.content).lower() or "three" in str(response.content).lower()
    )

    # Test OpenAI native format
    openai_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "How many people are in this CSV file?",
            },
            {
                "type": "input_file",
                "filename": "people.csv",
                "file_data": f"data:text/csv;base64,{base64_string}",
            },
        ],
    }
    payload2 = llm._get_request_payload([openai_message])
    block2 = payload2["input"][0]["content"][1]
    assert block2["type"] == "input_file"

    response2 = llm.invoke([openai_message])
    assert isinstance(response2, AIMessage)
    assert response2.content
    assert (
        "3" in str(response2.content).lower()
        or "three" in str(response2.content).lower()
    )