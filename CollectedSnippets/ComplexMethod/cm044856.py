def b_merge_audio(interval_r, *checkbox_list):
    global g_data_json, g_max_json_index
    b_save_file()
    checked_index = []
    audios_path = []
    audios_text = []
    for i, checkbox in enumerate(checkbox_list):
        if checkbox == True and g_index + i < len(g_data_json):
            checked_index.append(g_index + i)

    if len(checked_index) > 1:
        for i in checked_index:
            audios_path.append(g_data_json[i][g_json_key_path])
            audios_text.append(g_data_json[i][g_json_key_text])
        for i in reversed(checked_index[1:]):
            g_data_json.pop(i)

        base_index = checked_index[0]
        base_path = audios_path[0]
        g_data_json[base_index][g_json_key_text] = "".join(audios_text)

        audio_list = []
        l_sample_rate = None
        for i, path in enumerate(audios_path):
            data, sample_rate = librosa.load(path, sr=l_sample_rate, mono=True)
            l_sample_rate = sample_rate
            if i > 0:
                silence = np.zeros(int(l_sample_rate * interval_r))
                audio_list.append(silence)

            audio_list.append(data)

        audio_concat = np.concatenate(audio_list)

        soundfile.write(base_path, audio_concat, l_sample_rate)

        b_save_file()

    g_max_json_index = len(g_data_json) - 1

    # return gr.Slider(value=g_index, maximum=g_max_json_index), *b_change_index(g_index, g_batch)
    return {"value": g_index, "maximum": g_max_json_index, "__type__": "update"}, *b_change_index(g_index, g_batch)