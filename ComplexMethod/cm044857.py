def update_i18n_json(json_file, standard_keys):
    standard_keys = sorted(standard_keys)
    print(f" Process {json_file} ".center(TITLE_LEN, "="))
    # 读取 JSON 文件
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f, object_pairs_hook=OrderedDict)
    # 打印处理前的 JSON 条目数
    len_before = len(json_data)
    print(f"{'Total Keys'.ljust(KEY_LEN)}: {len_before}")
    # 识别缺失的键并补全
    miss_keys = set(standard_keys) - set(json_data.keys())
    if len(miss_keys) > 0:
        print(f"{'Missing Keys (+)'.ljust(KEY_LEN)}: {len(miss_keys)}")
        for key in miss_keys:
            if DEFAULT_LANGUAGE in json_file:
                # 默认语言的键值相同.
                json_data[key] = key
            else:
                # 其他语言的值设置为 #! + 键名以标注未被翻译.
                json_data[key] = "#!" + key
            if SHOW_KEYS:
                print(f"{'Added Missing Key'.ljust(KEY_LEN)}: {key}")
    # 识别多余的键并删除
    diff_keys = set(json_data.keys()) - set(standard_keys)
    if len(diff_keys) > 0:
        print(f"{'Unused Keys  (-)'.ljust(KEY_LEN)}: {len(diff_keys)}")
        for key in diff_keys:
            del json_data[key]
            if SHOW_KEYS:
                print(f"{'Removed Unused Key'.ljust(KEY_LEN)}: {key}")
    # 按键顺序排序
    json_data = OrderedDict(
        sorted(
            json_data.items(),
            key=lambda x: (
                list(standard_keys).index(x[0])
                if x[0] in standard_keys and not x[1].startswith("#!")
                else len(json_data),
            ),
        )
    )
    # 打印处理后的 JSON 条目数
    if len(miss_keys) != 0 or len(diff_keys) != 0:
        print(f"{'Total Keys (After)'.ljust(KEY_LEN)}: {len(json_data)}")
    # 识别有待翻译的键
    num_miss_translation = 0
    duplicate_items = {}
    for key, value in json_data.items():
        if value.startswith("#!"):
            num_miss_translation += 1
            if SHOW_KEYS:
                print(f"{'Missing Translation'.ljust(KEY_LEN)}: {key}")
        if value in duplicate_items:
            duplicate_items[value].append(key)
        else:
            duplicate_items[value] = [key]
    # 打印是否有重复的值
    for value, keys in duplicate_items.items():
        if len(keys) > 1:
            print(
                "\n".join(
                    [f"\033[31m{'[Failed] Duplicate Value'.ljust(KEY_LEN)}: {key} -> {value}\033[0m" for key in keys]
                )
            )

    if num_miss_translation > 0:
        print(f"\033[31m{'[Failed] Missing Translation'.ljust(KEY_LEN)}: {num_miss_translation}\033[0m")
    else:
        print("\033[32m[Passed] All Keys Translated\033[0m")
    # 将处理后的结果写入 JSON 文件
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4, sort_keys=SORT_KEYS)
        f.write("\n")
    print(f" Updated {json_file} ".center(TITLE_LEN, "=") + "\n")