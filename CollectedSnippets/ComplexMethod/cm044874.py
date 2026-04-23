def execute_asr(input_folder, output_folder, model_path, language, precision):
    if language == "auto":
        language = None  # 不设置语种由模型自动输出概率最高的语种
    print("loading faster whisper model:", model_path, model_path)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = WhisperModel(model_path, device=device, compute_type=precision)

    input_file_names = os.listdir(input_folder)
    input_file_names.sort()

    output = []
    output_file_name = os.path.basename(input_folder)

    for file_name in tqdm(input_file_names):
        try:
            file_path = os.path.join(input_folder, file_name)
            segments, info = model.transcribe(
                audio=file_path,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=700),
                language=language,
            )
            text = ""

            if info.language in ["zh", "yue"]:
                print("检测为中文文本, 转 FunASR 处理")
                text = only_asr(file_path, language=info.language.lower())

            if text == "":
                for segment in segments:
                    text += segment.text
            output.append(f"{file_path}|{output_file_name}|{info.language.upper()}|{text}")
        except Exception as e:
            print(e)
            traceback.print_exc()

    output_folder = output_folder or "output/asr_opt"
    os.makedirs(output_folder, exist_ok=True)
    output_file_path = os.path.abspath(f"{output_folder}/{output_file_name}.list")

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))
        print(f"ASR 任务完成->标注文件路径: {output_file_path}\n")
    return output_file_path