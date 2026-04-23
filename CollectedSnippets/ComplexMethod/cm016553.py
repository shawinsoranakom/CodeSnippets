def load_text_encoder_state_dicts(state_dicts=[], embedding_directory=None, clip_type=CLIPType.STABLE_DIFFUSION, model_options={}, disable_dynamic=False):
    clip_data = state_dicts

    class EmptyClass:
        pass

    for i in range(len(clip_data)):
        if "transformer.resblocks.0.ln_1.weight" in clip_data[i]:
            clip_data[i] = comfy.utils.clip_text_transformers_convert(clip_data[i], "", "")
        else:
            if "text_projection" in clip_data[i]:
                clip_data[i]["text_projection.weight"] = clip_data[i]["text_projection"].transpose(0, 1) #old models saved with the CLIPSave node
        if "lm_head.weight" in clip_data[i]:
            clip_data[i]["model.lm_head.weight"] = clip_data[i].pop("lm_head.weight") # prefix missing in some models

    tokenizer_data = {}
    clip_target = EmptyClass()
    clip_target.params = {}
    if len(clip_data) == 1:
        te_model = detect_te_model(clip_data[0])
        if te_model == TEModel.CLIP_G:
            if clip_type == CLIPType.STABLE_CASCADE:
                clip_target.clip = sdxl_clip.StableCascadeClipModel
                clip_target.tokenizer = sdxl_clip.StableCascadeTokenizer
            elif clip_type == CLIPType.SD3:
                clip_target.clip = comfy.text_encoders.sd3_clip.sd3_clip(clip_l=False, clip_g=True, t5=False)
                clip_target.tokenizer = comfy.text_encoders.sd3_clip.SD3Tokenizer
            elif clip_type == CLIPType.HIDREAM:
                clip_target.clip = comfy.text_encoders.hidream.hidream_clip(clip_l=False, clip_g=True, t5=False, llama=False, dtype_t5=None, dtype_llama=None)
                clip_target.tokenizer = comfy.text_encoders.hidream.HiDreamTokenizer
            else:
                clip_target.clip = sdxl_clip.SDXLRefinerClipModel
                clip_target.tokenizer = sdxl_clip.SDXLTokenizer
        elif te_model == TEModel.CLIP_H:
            clip_target.clip = comfy.text_encoders.sd2_clip.SD2ClipModel
            clip_target.tokenizer = comfy.text_encoders.sd2_clip.SD2Tokenizer
        elif te_model == TEModel.T5_XXL:
            if clip_type == CLIPType.SD3:
                clip_target.clip = comfy.text_encoders.sd3_clip.sd3_clip(clip_l=False, clip_g=False, t5=True, **t5xxl_detect(clip_data))
                clip_target.tokenizer = comfy.text_encoders.sd3_clip.SD3Tokenizer
            elif clip_type == CLIPType.LTXV:
                clip_target.clip = comfy.text_encoders.lt.ltxv_te(**t5xxl_detect(clip_data))
                clip_target.tokenizer = comfy.text_encoders.lt.LTXVT5Tokenizer
            elif clip_type == CLIPType.PIXART or clip_type == CLIPType.CHROMA:
                clip_target.clip = comfy.text_encoders.pixart_t5.pixart_te(**t5xxl_detect(clip_data))
                clip_target.tokenizer = comfy.text_encoders.pixart_t5.PixArtTokenizer
            elif clip_type == CLIPType.WAN:
                clip_target.clip = comfy.text_encoders.wan.te(**t5xxl_detect(clip_data))
                clip_target.tokenizer = comfy.text_encoders.wan.WanT5Tokenizer
                tokenizer_data["spiece_model"] = clip_data[0].get("spiece_model", None)
            elif clip_type == CLIPType.HIDREAM:
                clip_target.clip = comfy.text_encoders.hidream.hidream_clip(**t5xxl_detect(clip_data),
                                                                        clip_l=False, clip_g=False, t5=True, llama=False, dtype_llama=None)
                clip_target.tokenizer = comfy.text_encoders.hidream.HiDreamTokenizer
            else: #CLIPType.MOCHI
                clip_target.clip = comfy.text_encoders.genmo.mochi_te(**t5xxl_detect(clip_data))
                clip_target.tokenizer = comfy.text_encoders.genmo.MochiT5Tokenizer
        elif te_model == TEModel.T5_XXL_OLD:
            clip_target.clip = comfy.text_encoders.cosmos.te(**t5xxl_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.cosmos.CosmosT5Tokenizer
        elif te_model == TEModel.T5_XL:
            clip_target.clip = comfy.text_encoders.aura_t5.AuraT5Model
            clip_target.tokenizer = comfy.text_encoders.aura_t5.AuraT5Tokenizer
        elif te_model == TEModel.T5_BASE:
            if clip_type == CLIPType.ACE or "spiece_model" in clip_data[0]:
                clip_target.clip = comfy.text_encoders.ace.AceT5Model
                clip_target.tokenizer = comfy.text_encoders.ace.AceT5Tokenizer
                tokenizer_data["spiece_model"] = clip_data[0].get("spiece_model", None)
            else:
                clip_target.clip = comfy.text_encoders.sa_t5.SAT5Model
                clip_target.tokenizer = comfy.text_encoders.sa_t5.SAT5Tokenizer
        elif te_model == TEModel.GEMMA_2_2B:
            clip_target.clip = comfy.text_encoders.lumina2.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.lumina2.LuminaTokenizer
            tokenizer_data["spiece_model"] = clip_data[0].get("spiece_model", None)
        elif te_model == TEModel.GEMMA_3_4B:
            clip_target.clip = comfy.text_encoders.lumina2.te(**llama_detect(clip_data), model_type="gemma3_4b")
            clip_target.tokenizer = comfy.text_encoders.lumina2.NTokenizer
            tokenizer_data["spiece_model"] = clip_data[0].get("spiece_model", None)
        elif te_model == TEModel.GEMMA_3_4B_VISION:
            clip_target.clip = comfy.text_encoders.lumina2.te(**llama_detect(clip_data), model_type="gemma3_4b_vision")
            clip_target.tokenizer = comfy.text_encoders.lumina2.NTokenizer
            tokenizer_data["spiece_model"] = clip_data[0].get("spiece_model", None)
        elif te_model == TEModel.GEMMA_3_12B:
            clip_target.clip = comfy.text_encoders.lt.gemma3_te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.lt.Gemma3_12BTokenizer
            tokenizer_data["spiece_model"] = clip_data[0].get("spiece_model", None)
        elif te_model == TEModel.LLAMA3_8:
            clip_target.clip = comfy.text_encoders.hidream.hidream_clip(**llama_detect(clip_data),
                                                                        clip_l=False, clip_g=False, t5=False, llama=True, dtype_t5=None)
            clip_target.tokenizer = comfy.text_encoders.hidream.HiDreamTokenizer
        elif te_model == TEModel.QWEN25_3B:
            clip_target.clip = comfy.text_encoders.omnigen2.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.omnigen2.Omnigen2Tokenizer
        elif te_model == TEModel.QWEN25_7B:
            if clip_type == CLIPType.HUNYUAN_IMAGE:
                clip_target.clip = comfy.text_encoders.hunyuan_image.te(byt5=False, **llama_detect(clip_data))
                clip_target.tokenizer = comfy.text_encoders.hunyuan_image.HunyuanImageTokenizer
            elif clip_type == CLIPType.LONGCAT_IMAGE:
                clip_target.clip = comfy.text_encoders.longcat_image.te(**llama_detect(clip_data))
                clip_target.tokenizer = comfy.text_encoders.longcat_image.LongCatImageTokenizer
            else:
                clip_target.clip = comfy.text_encoders.qwen_image.te(**llama_detect(clip_data))
                clip_target.tokenizer = comfy.text_encoders.qwen_image.QwenImageTokenizer
        elif te_model == TEModel.MISTRAL3_24B or te_model == TEModel.MISTRAL3_24B_PRUNED_FLUX2:
            clip_target.clip = comfy.text_encoders.flux.flux2_te(**llama_detect(clip_data), pruned=te_model == TEModel.MISTRAL3_24B_PRUNED_FLUX2)
            clip_target.tokenizer = comfy.text_encoders.flux.Flux2Tokenizer
            tokenizer_data["tekken_model"] = clip_data[0].get("tekken_model", None)
        elif te_model == TEModel.QWEN3_4B:
            if clip_type == CLIPType.FLUX or clip_type == CLIPType.FLUX2:
                clip_target.clip = comfy.text_encoders.flux.klein_te(**llama_detect(clip_data), model_type="qwen3_4b")
                clip_target.tokenizer = comfy.text_encoders.flux.KleinTokenizer
            else:
                clip_target.clip = comfy.text_encoders.z_image.te(**llama_detect(clip_data))
                clip_target.tokenizer = comfy.text_encoders.z_image.ZImageTokenizer
        elif te_model == TEModel.QWEN3_2B:
            clip_target.clip = comfy.text_encoders.ovis.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.ovis.OvisTokenizer
        elif te_model == TEModel.QWEN3_8B:
            clip_target.clip = comfy.text_encoders.flux.klein_te(**llama_detect(clip_data), model_type="qwen3_8b")
            clip_target.tokenizer = comfy.text_encoders.flux.KleinTokenizer8B
        elif te_model == TEModel.JINA_CLIP_2:
            clip_target.clip = comfy.text_encoders.jina_clip_2.JinaClip2TextModelWrapper
            clip_target.tokenizer = comfy.text_encoders.jina_clip_2.JinaClip2TokenizerWrapper
        elif te_model in (TEModel.QWEN35_08B, TEModel.QWEN35_2B, TEModel.QWEN35_4B, TEModel.QWEN35_9B, TEModel.QWEN35_27B):
            clip_data[0] = comfy.utils.state_dict_prefix_replace(clip_data[0], {"model.language_model.": "model.", "model.visual.": "visual.", "lm_head.": "model.lm_head."})
            qwen35_type = {TEModel.QWEN35_08B: "qwen35_08b", TEModel.QWEN35_2B: "qwen35_2b", TEModel.QWEN35_4B: "qwen35_4b", TEModel.QWEN35_9B: "qwen35_9b", TEModel.QWEN35_27B: "qwen35_27b"}[te_model]
            clip_target.clip = comfy.text_encoders.qwen35.te(**llama_detect(clip_data), model_type=qwen35_type)
            clip_target.tokenizer = comfy.text_encoders.qwen35.tokenizer(model_type=qwen35_type)
        elif te_model == TEModel.QWEN3_06B:
            clip_target.clip = comfy.text_encoders.anima.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.anima.AnimaTokenizer
        elif te_model == TEModel.MINISTRAL_3_3B:
            clip_target.clip = comfy.text_encoders.ernie.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.ernie.ErnieTokenizer
            tokenizer_data["tekken_model"] = clip_data[0].get("tekken_model", None)
        else:
            # clip_l
            if clip_type == CLIPType.SD3:
                clip_target.clip = comfy.text_encoders.sd3_clip.sd3_clip(clip_l=True, clip_g=False, t5=False)
                clip_target.tokenizer = comfy.text_encoders.sd3_clip.SD3Tokenizer
            elif clip_type == CLIPType.HIDREAM:
                clip_target.clip = comfy.text_encoders.hidream.hidream_clip(clip_l=True, clip_g=False, t5=False, llama=False, dtype_t5=None, dtype_llama=None)
                clip_target.tokenizer = comfy.text_encoders.hidream.HiDreamTokenizer
            else:
                clip_target.clip = sd1_clip.SD1ClipModel
                clip_target.tokenizer = sd1_clip.SD1Tokenizer
    elif len(clip_data) == 2:
        if clip_type == CLIPType.SD3:
            te_models = [detect_te_model(clip_data[0]), detect_te_model(clip_data[1])]
            clip_target.clip = comfy.text_encoders.sd3_clip.sd3_clip(clip_l=TEModel.CLIP_L in te_models, clip_g=TEModel.CLIP_G in te_models, t5=TEModel.T5_XXL in te_models, **t5xxl_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.sd3_clip.SD3Tokenizer
        elif clip_type == CLIPType.HUNYUAN_DIT:
            clip_target.clip = comfy.text_encoders.hydit.HyditModel
            clip_target.tokenizer = comfy.text_encoders.hydit.HyditTokenizer
        elif clip_type == CLIPType.FLUX:
            clip_target.clip = comfy.text_encoders.flux.flux_clip(**t5xxl_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.flux.FluxTokenizer
        elif clip_type == CLIPType.HUNYUAN_VIDEO:
            clip_target.clip = comfy.text_encoders.hunyuan_video.hunyuan_video_clip(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.hunyuan_video.HunyuanVideoTokenizer
        elif clip_type == CLIPType.HIDREAM:
            # Detect
            hidream_dualclip_classes = []
            for hidream_te in clip_data:
                te_model = detect_te_model(hidream_te)
                hidream_dualclip_classes.append(te_model)

            clip_l = TEModel.CLIP_L in hidream_dualclip_classes
            clip_g = TEModel.CLIP_G in hidream_dualclip_classes
            t5 = TEModel.T5_XXL in hidream_dualclip_classes
            llama = TEModel.LLAMA3_8 in hidream_dualclip_classes

            # Initialize t5xxl_detect and llama_detect kwargs if needed
            t5_kwargs = t5xxl_detect(clip_data) if t5 else {}
            llama_kwargs = llama_detect(clip_data) if llama else {}

            clip_target.clip = comfy.text_encoders.hidream.hidream_clip(clip_l=clip_l, clip_g=clip_g, t5=t5, llama=llama, **t5_kwargs, **llama_kwargs)
            clip_target.tokenizer = comfy.text_encoders.hidream.HiDreamTokenizer
        elif clip_type == CLIPType.HUNYUAN_IMAGE:
            clip_target.clip = comfy.text_encoders.hunyuan_image.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.hunyuan_image.HunyuanImageTokenizer
        elif clip_type == CLIPType.HUNYUAN_VIDEO_15:
            clip_target.clip = comfy.text_encoders.hunyuan_image.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.hunyuan_video.HunyuanVideo15Tokenizer
        elif clip_type == CLIPType.KANDINSKY5:
            clip_target.clip = comfy.text_encoders.kandinsky5.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.kandinsky5.Kandinsky5Tokenizer
        elif clip_type == CLIPType.KANDINSKY5_IMAGE:
            clip_target.clip = comfy.text_encoders.kandinsky5.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.kandinsky5.Kandinsky5TokenizerImage
        elif clip_type == CLIPType.LTXV:
            clip_target.clip = comfy.text_encoders.lt.ltxav_te(**llama_detect(clip_data), **comfy.text_encoders.lt.sd_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.lt.LTXAVGemmaTokenizer
            tokenizer_data["spiece_model"] = clip_data[0].get("spiece_model", None)
        elif clip_type == CLIPType.NEWBIE:
            clip_target.clip = comfy.text_encoders.newbie.te(**llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.newbie.NewBieTokenizer
            if "model.layers.0.self_attn.q_norm.weight" in clip_data[0]:
                clip_data_gemma = clip_data[0]
                clip_data_jina = clip_data[1]
            else:
                clip_data_gemma = clip_data[1]
                clip_data_jina = clip_data[0]
            tokenizer_data["gemma_spiece_model"] = clip_data_gemma.get("spiece_model", None)
            tokenizer_data["jina_spiece_model"] = clip_data_jina.get("spiece_model", None)
        elif clip_type == CLIPType.ACE:
            te_models = [detect_te_model(clip_data[0]), detect_te_model(clip_data[1])]
            if TEModel.QWEN3_4B in te_models:
                model_type = "qwen3_4b"
            else:
                model_type = "qwen3_2b"
            clip_target.clip = comfy.text_encoders.ace15.te(lm_model=model_type, **llama_detect(clip_data))
            clip_target.tokenizer = comfy.text_encoders.ace15.ACE15Tokenizer
        else:
            clip_target.clip = sdxl_clip.SDXLClipModel
            clip_target.tokenizer = sdxl_clip.SDXLTokenizer
    elif len(clip_data) == 3:
        clip_target.clip = comfy.text_encoders.sd3_clip.sd3_clip(**t5xxl_detect(clip_data))
        clip_target.tokenizer = comfy.text_encoders.sd3_clip.SD3Tokenizer
    elif len(clip_data) == 4:
        clip_target.clip = comfy.text_encoders.hidream.hidream_clip(**t5xxl_detect(clip_data), **llama_detect(clip_data))
        clip_target.tokenizer = comfy.text_encoders.hidream.HiDreamTokenizer

    parameters = 0
    for c in clip_data:
        parameters += comfy.utils.calculate_parameters(c)
        tokenizer_data, model_options = comfy.text_encoders.long_clipl.model_options_long_clip(c, tokenizer_data, model_options)

    clip = CLIP(clip_target, embedding_directory=embedding_directory, parameters=parameters, tokenizer_data=tokenizer_data, state_dict=clip_data, model_options=model_options, disable_dynamic=disable_dynamic)
    return clip