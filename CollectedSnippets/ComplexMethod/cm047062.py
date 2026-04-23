def populate_legacy_submaker_with_full_text(
    sub_maker: SubMaker, text: str, audio_duration_seconds: float
) -> SubMaker:
    """
    用整段文本填充项目历史沿用的 `subs/offset` 字幕结构。

    背景：
    1. edge_tts 7.x 的 `SubMaker` 不再提供旧版本里的 `create_sub()`；
    2. 项目里 Gemini、SiliconFlow 等非 edge 路径依然需要返回一个
       带 `subs/offset` 的对象，供后续统一计算音频时长和生成字幕；
    3. 对于拿不到逐词边界的 TTS 服务，需要至少按脚本断句切成多个片段，
       这样后续 `subtitle_provider=edge` 的聚合逻辑才能继续工作，而不是
       因为整段文本无法和脚本断句逐行匹配而回退 Whisper。

    Args:
        sub_maker: 需要写入兼容字段的字幕对象
        text: 原始脚本文本
        audio_duration_seconds: 音频总时长，单位秒

    Returns:
        已填充兼容字幕数据的 SubMaker 对象
    """
    sub_maker = ensure_legacy_submaker_fields(sub_maker)

    # 清空旧值，避免调用方重复复用对象时出现脏数据叠加。
    sub_maker.subs = []
    sub_maker.offset = []

    normalized_text = (text or "").strip()
    if not normalized_text:
        return sub_maker

    audio_duration_100ns = max(int(audio_duration_seconds * 10000000), 1)

    # Gemini / SiliconFlow 这类路径拿不到逐词边界时，仍然尽量沿用项目
    # 原来的“按标点断句 + 按字符数比例分配时长”的策略。这样既能让
    # create_subtitle() 匹配脚本断句，也能避免再次回退 Whisper。
    sentences = utils.split_string_by_punctuations(normalized_text)
    if not sentences:
        sentences = [normalized_text]

    total_chars = sum(len(sentence) for sentence in sentences)
    if total_chars <= 0:
        sub_maker.subs.append(normalized_text)
        sub_maker.offset.append((0, audio_duration_100ns))
        return sub_maker

    current_offset = 0
    for index, sentence in enumerate(sentences):
        cleaned_sentence = sentence.strip()
        if not cleaned_sentence:
            continue

        # 前面的句子按字符数比例分配时长，最后一句兜底吃掉剩余时长，
        # 避免整数取整导致总时长丢失或字幕结束时间短于音频。
        if index == len(sentences) - 1:
            sentence_end = audio_duration_100ns
        else:
            sentence_chars = len(cleaned_sentence)
            sentence_duration = max(
                int(audio_duration_100ns * (sentence_chars / total_chars)),
                1,
            )
            sentence_end = min(current_offset + sentence_duration, audio_duration_100ns)

        sub_maker.subs.append(cleaned_sentence)
        sub_maker.offset.append((current_offset, sentence_end))
        current_offset = sentence_end

    return sub_maker