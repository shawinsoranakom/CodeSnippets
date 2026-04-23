def handle_change(path, text, language):
    if is_empty(path, text, language):
        return JSONResponse(
            {"code": 400, "message": '缺少任意一项以下参数: "path", "text", "language"'}, status_code=400
        )

    if path != "" or path is not None:
        default_refer.path = path
    if text != "" or text is not None:
        default_refer.text = text
    if language != "" or language is not None:
        default_refer.language = language

    logger.info(f"当前默认参考音频路径: {default_refer.path}")
    logger.info(f"当前默认参考音频文本: {default_refer.text}")
    logger.info(f"当前默认参考音频语种: {default_refer.language}")
    logger.info(f"is_ready: {default_refer.is_ready()}")

    return JSONResponse({"code": 0, "message": "Success"}, status_code=200)