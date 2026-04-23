def test_hallucinations():
    # We should be resiliant to common hallucinations.

    code = """10+12executeexecute\n"""

    interpreter.messages = [
        {"role": "assistant", "type": "code", "format": "python", "content": code}
    ]
    for chunk in interpreter._respond_and_store():
        if chunk.get("format") == "output":
            assert chunk.get("content") == "22"
            break

    code = """{                                                                             
    "language": "python",                                                        
    "code": "10+12"                                                        
  }"""

    interpreter.messages = [
        {"role": "assistant", "type": "code", "format": "python", "content": code}
    ]
    for chunk in interpreter._respond_and_store():
        if chunk.get("format") == "output":
            assert chunk.get("content") == "22"
            break

    code = """functions.execute({                                                                             
    "language": "python",                                                        
    "code": "10+12"                                                        
  })"""

    interpreter.messages = [
        {"role": "assistant", "type": "code", "format": "python", "content": code}
    ]
    for chunk in interpreter._respond_and_store():
        if chunk.get("format") == "output":
            assert chunk.get("content") == "22"
            break

    code = """{language: "python", code: "print('hello')" }"""

    interpreter.messages = [
        {"role": "assistant", "type": "code", "format": "python", "content": code}
    ]
    for chunk in interpreter._respond_and_store():
        if chunk.get("format") == "output":
            assert chunk.get("content").strip() == "hello"
            break