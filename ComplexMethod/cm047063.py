def siliconflow_tts(
    text: str,
    model: str,
    voice: str,
    voice_rate: float,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用硅基流动的API生成语音

    Args:
        text: 要转换为语音的文本
        model: 模型名称，如 "FunAudioLLM/CosyVoice2-0.5B"
        voice: 声音名称，如 "FunAudioLLM/CosyVoice2-0.5B:alex"
        voice_rate: 语音速度，范围[0.25, 4.0]
        voice_file: 输出的音频文件路径
        voice_volume: 语音音量，范围[0.6, 5.0]，需要转换为硅基流动的增益范围[-10, 10]

    Returns:
        SubMaker对象或None
    """
    text = text.strip()
    api_key = config.siliconflow.get("api_key", "")

    if not api_key:
        logger.error("SiliconFlow API key is not set")
        return None

    # 将voice_volume转换为硅基流动的增益范围
    # 默认voice_volume为1.0，对应gain为0
    gain = voice_volume - 1.0
    # 确保gain在[-10, 10]范围内
    gain = max(-10, min(10, gain))

    url = "https://api.siliconflow.cn/v1/audio/speech"

    payload = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": "mp3",
        "sample_rate": 32000,
        "stream": False,
        "speed": voice_rate,
        "gain": gain,
    }

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for i in range(3):  # 尝试3次
        try:
            logger.info(
                f"start siliconflow tts, model: {model}, voice: {voice}, try: {i + 1}"
            )

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                # 保存音频文件
                with open(voice_file, "wb") as f:
                    f.write(response.content)

                # 这里仍然沿用项目原有的字幕结构，因此需要补齐旧字段。
                sub_maker = ensure_legacy_submaker_fields(SubMaker())

                # 获取音频文件的实际长度
                try:
                    # 尝试使用moviepy获取音频长度
                    from moviepy import AudioFileClip

                    audio_clip = AudioFileClip(voice_file)
                    audio_duration = audio_clip.duration
                    audio_clip.close()

                    # 将音频长度转换为100纳秒单位（与edge_tts兼容）
                    audio_duration_100ns = int(audio_duration * 10000000)

                    # 使用文本分割来创建更准确的字幕
                    # 将文本按标点符号分割成句子
                    sentences = utils.split_string_by_punctuations(text)

                    if sentences:
                        # 计算每个句子的大致时长（按字符数比例分配）
                        total_chars = sum(len(s) for s in sentences)
                        char_duration = (
                            audio_duration_100ns / total_chars if total_chars > 0 else 0
                        )

                        current_offset = 0
                        for sentence in sentences:
                            if not sentence.strip():
                                continue

                            # 计算当前句子的时长
                            sentence_chars = len(sentence)
                            sentence_duration = int(sentence_chars * char_duration)

                            # 添加到SubMaker
                            sub_maker.subs.append(sentence)
                            sub_maker.offset.append(
                                (current_offset, current_offset + sentence_duration)
                            )

                            # 更新偏移量
                            current_offset += sentence_duration
                    else:
                        # 如果无法分割，则使用整个文本作为一个字幕
                        sub_maker.subs = [text]
                        sub_maker.offset = [(0, audio_duration_100ns)]

                except Exception as e:
                    logger.warning(f"Failed to create accurate subtitles: {str(e)}")
                    # 回退到简单的字幕
                    sub_maker.subs = [text]
                    # 使用音频文件的实际长度，如果无法获取，则假设为10秒
                    sub_maker.offset = [
                        (
                            0,
                            audio_duration_100ns
                            if "audio_duration_100ns" in locals()
                            else 10000000,
                        )
                    ]

                logger.success(f"siliconflow tts succeeded: {voice_file}")
                print("s", sub_maker.subs, sub_maker.offset)
                return sub_maker
            else:
                logger.error(
                    f"siliconflow tts failed with status code {response.status_code}: {response.text}"
                )
        except Exception as e:
            logger.error(f"siliconflow tts failed: {str(e)}")

    return None