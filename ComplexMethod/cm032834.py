def chunk(filename, binary, tenant_id, lang, callback=None, **kwargs):
    doc = {
        "docnm_kwd": filename,
        "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", filename)),
    }
    eng = lang.lower() == "english"

    parser_config = kwargs.get("parser_config", {}) or {}
    image_ctx = max(0, int(parser_config.get("image_context_size", 0) or 0))

    if any(filename.lower().endswith(ext) for ext in VIDEO_EXTS):
        try:
            doc.update(
                {
                    "doc_type_kwd": "video",
                }
            )
            cv_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.IMAGE2TEXT)
            cv_mdl = LLMBundle(tenant_id, model_config=cv_model_config, lang=lang)
            video_prompt = str(parser_config.get("video_prompt", "") or "")
            ans = asyncio.run(
                cv_mdl.async_chat(system="", history=[], gen_conf={}, video_bytes=binary, filename=filename, video_prompt=video_prompt))
            callback(0.8, "CV LLM respond: %s ..." % ans[:32])
            ans += "\n" + ans
            tokenize(doc, ans, eng)
            return [doc]
        except Exception as e:
            callback(prog=-1, msg=str(e))
    else:
        img = Image.open(io.BytesIO(binary)).convert("RGB")
        doc.update(
            {
                "image": img,
                "doc_type_kwd": "image",
            }
        )
        bxs = ocr(np.array(img))
        txt = "\n".join([t[0] for _, t in bxs if t[0]])
        callback(0.4, "Finish OCR: (%s ...)" % txt[:12])
        if (eng and len(txt.split()) > 32) or len(txt) > 32:
            tokenize(doc, txt, eng)
            callback(0.8, "OCR results is too long to use CV LLM.")
            return attach_media_context([doc], 0, image_ctx)

        try:
            callback(0.4, "Use CV LLM to describe the picture.")
            cv_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.IMAGE2TEXT)
            cv_mdl = LLMBundle(tenant_id, model_config=cv_model_config, lang=lang)
            with io.BytesIO() as img_binary:
                img.save(img_binary, format="JPEG")
                img_binary.seek(0)
                ans = cv_mdl.describe(img_binary.read())
            callback(0.8, "CV LLM respond: %s ..." % ans[:32])
            txt += "\n" + ans
            tokenize(doc, txt, eng)
            return attach_media_context([doc], 0, image_ctx)
        except Exception as e:
            callback(prog=-1, msg=str(e))

    return []