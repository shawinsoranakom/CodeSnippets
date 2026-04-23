def test_message_serdeser_from_basecontext():
    doc_msg = Message(content="test_document", instruct_content=Document(content="test doc"))
    ser_data = doc_msg.model_dump()
    assert ser_data["instruct_content"]["value"]["content"] == "test doc"
    assert ser_data["instruct_content"]["value"]["filename"] == ""

    docs_msg = Message(
        content="test_documents", instruct_content=Documents(docs={"doc1": Document(content="test doc")})
    )
    ser_data = docs_msg.model_dump()
    assert ser_data["instruct_content"]["class"] == "Documents"
    assert ser_data["instruct_content"]["value"]["docs"]["doc1"]["content"] == "test doc"
    assert ser_data["instruct_content"]["value"]["docs"]["doc1"]["filename"] == ""

    code_ctxt = CodingContext(
        filename="game.py",
        design_doc=Document(root_path="docs/system_design", filename="xx.json", content="xxx"),
        task_doc=Document(root_path="docs/tasks", filename="xx.json", content="xxx"),
        code_doc=Document(root_path="xxx", filename="game.py", content="xxx"),
    )
    code_ctxt_msg = Message(content="coding_context", instruct_content=code_ctxt)
    ser_data = code_ctxt_msg.model_dump()
    assert ser_data["instruct_content"]["class"] == "CodingContext"

    new_code_ctxt_msg = Message(**ser_data)
    assert new_code_ctxt_msg.instruct_content == code_ctxt
    assert new_code_ctxt_msg.instruct_content.code_doc.filename == "game.py"
    assert new_code_ctxt_msg == code_ctxt_msg

    testing_ctxt = TestingContext(
        filename="test.py",
        code_doc=Document(root_path="xxx", filename="game.py", content="xxx"),
        test_doc=Document(root_path="docs/tests", filename="test.py", content="xxx"),
    )
    testing_ctxt_msg = Message(content="testing_context", instruct_content=testing_ctxt)
    ser_data = testing_ctxt_msg.model_dump()
    new_testing_ctxt_msg = Message(**ser_data)
    assert new_testing_ctxt_msg.instruct_content == testing_ctxt
    assert new_testing_ctxt_msg.instruct_content.test_doc.filename == "test.py"
    assert new_testing_ctxt_msg == testing_ctxt_msg