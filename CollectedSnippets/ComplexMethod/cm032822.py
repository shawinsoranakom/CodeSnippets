def column_data_type(arr):
    arr = list(arr)
    counts = {"int": 0, "float": 0, "text": 0, "datetime": 0, "bool": 0}
    trans = {t: f for f, t in
             [(int, "int"), (float, "float"), (trans_datatime, "datetime"), (trans_bool, "bool"), (str, "text")]}
    float_flag = False
    for a in arr:
        if a is None:
            continue
        if re.match(r"[+-]?[0-9]+$", str(a).replace("%%", "")) and not str(a).replace("%%", "").startswith("0"):
            counts["int"] += 1
            if int(str(a)) > 2 ** 63 - 1:
                float_flag = True
                break
        elif re.match(r"[+-]?[0-9.]{,19}$", str(a).replace("%%", "")) and not str(a).replace("%%", "").startswith("0"):
            counts["float"] += 1
        elif re.match(r"(true|yes|是|\*|✓|✔|☑|✅|√|false|no|否|⍻|×)$", str(a), flags=re.IGNORECASE):
            counts["bool"] += 1
        elif trans_datatime(str(a)):
            counts["datetime"] += 1
        else:
            counts["text"] += 1
    if float_flag:
        ty = "float"
    else:
        counts = sorted(counts.items(), key=lambda x: x[1] * -1)
        ty = counts[0][0]
    for i in range(len(arr)):
        if arr[i] is None:
            continue
        try:
            arr[i] = trans[ty](str(arr[i]))
        except Exception as e:
            arr[i] = None
            logging.warning(f"Column {i}: {e}")
    # if ty == "text":
    #    if len(arr) > 128 and uni / len(arr) < 0.1:
    #        ty = "keyword"
    return arr, ty