def handle(
    refer_wav_path,
    prompt_text,
    prompt_language,
    text,
    text_language,
    cut_punc,
    top_k,
    top_p,
    temperature,
    speed,
    inp_refs,
    sample_steps,
    if_sr,
):
    if (
        refer_wav_path == ""
        or refer_wav_path is None
        or prompt_text == ""
        or prompt_text is None
        or prompt_language == ""
        or prompt_language is None
    ):
        refer_wav_path, prompt_text, prompt_language = (
            default_refer.path,
            default_refer.text,
            default_refer.language,
        )
        if not default_refer.is_ready():
            return JSONResponse({"code": 400, "message": "未指定参考音频且接口无预设"}, status_code=400)

    if cut_punc == None:
        text = cut_text(text, default_cut_punc)
    else:
        text = cut_text(text, cut_punc)

    return StreamingResponse(
        get_tts_wav(
            refer_wav_path,
            prompt_text,
            prompt_language,
            text,
            text_language,
            top_k,
            top_p,
            temperature,
            speed,
            inp_refs,
            sample_steps,
            if_sr,
        ),
        media_type="audio/" + media_type,
    )