def decode_chunk(chunk):
    """
    用于解读"content"和"finish_reason"的内容（如果支持思维链也会返回"reasoning_content"内容）
    """
    chunk = chunk.decode()
    response = ""
    reasoning_content = ""
    finish_reason = "False"

    # 考虑返回类型是 text/json 和 text/event-stream 两种
    if chunk.startswith("data: "):
        chunk = chunk[6:]
    else:
        chunk = chunk

    try:
        chunk = json.loads(chunk)
    except:
        response = ""
        finish_reason = chunk

    # 错误处理部分
    if "error" in chunk:
        response = "API_ERROR"
        try:
            chunk = json.loads(chunk)
            finish_reason = chunk["error"]["code"]
        except:
            finish_reason = "API_ERROR"
        return response, reasoning_content, finish_reason, str(chunk)

    try:
        if chunk["choices"][0]["delta"]["content"] is not None:
            response = chunk["choices"][0]["delta"]["content"]
    except:
        pass
    try:
        if chunk["choices"][0]["delta"]["reasoning_content"] is not None:
            reasoning_content = chunk["choices"][0]["delta"]["reasoning_content"]
    except:
        pass
    try:
        finish_reason = chunk["choices"][0]["finish_reason"]
    except:
        pass
    return response, reasoning_content, finish_reason, str(chunk)