def gemini_tts(
    text: str,
    voice_name: str,
    voice_rate: float,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用Google Gemini TTS生成语音

    Args:
        text: 要转换的文本
        voice_name: 语音名称，如 "Zephyr", "Puck" 等
        voice_rate: 语音速率（当前未使用）
        voice_file: 输出音频文件路径
        voice_volume: 音频音量（当前未使用）

    Returns:
        SubMaker对象或None
    """
    import base64
    import json
    import io
    from pydub import AudioSegment
    import google.generativeai as genai

    try:
        # 配置Gemini API
        api_key = config.app.get("gemini_api_key", "")
        if not api_key:
            logger.error("Gemini API key is not set")
            return None

        genai.configure(api_key=api_key)

        logger.info(f"start, voice name: {voice_name}, try: 1")

        # 使用Gemini TTS API
        model = genai.GenerativeModel("gemini-2.5-flash-preview-tts")

        generation_config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": voice_name
                    }
                }
            }
        }

        response = model.generate_content(
            contents=text,
            generation_config=generation_config
        )

        # 检查响应
        if not response.candidates or not response.candidates[0].content:
            logger.error("No audio content received from Gemini TTS")
            return None

        # 获取音频数据
        audio_data = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                audio_data = part.inline_data.data
                break

        if not audio_data:
            logger.error("No audio data found in response")
            return None

        # 音频数据已经是原始字节，不需要base64解码
        if isinstance(audio_data, str):
            # 如果是字符串，则需要base64解码
            audio_bytes = base64.b64decode(audio_data)
        else:
            # 如果已经是字节，直接使用
            audio_bytes = audio_data

        # 尝试不同的音频格式 - Gemini可能返回不同的格式
        audio_segment = None

        # Gemini返回Linear PCM格式，按照文档参数解析
        try:
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_bytes), 
                format="raw",
                frame_rate=24000,  # Gemini TTS默认采样率
                channels=1,        # 单声道
                sample_width=2     # 16-bit
            )
        except Exception as e:
            logger.error(f"Failed to load PCM audio: {e}")
            return None

        # 导出为MP3格式
        audio_segment.export(voice_file, format="mp3")

        logger.info(f"completed, output file: {voice_file}")

        # Gemini 拿不到 edge_tts 那种逐词边界事件，因此这里退回到
        # 项目原有的 `subs/offset` 兼容结构，至少保证后续字幕与时长
        # 计算链路可继续工作。
        sub_maker = ensure_legacy_submaker_fields(SubMaker())
        audio_duration = len(audio_segment) / 1000.0  # 转换为秒
        return populate_legacy_submaker_with_full_text(
            sub_maker=sub_maker,
            text=text,
            audio_duration_seconds=audio_duration,
        )

    except ImportError as e:
        logger.error(f"Missing required package for Gemini TTS: {str(e)}. Please install: pip install pydub")
        return None
    except Exception as e:
        logger.error(f"Gemini TTS failed, error: {str(e)}")
        return None