def parse_ser_results_fp(fp, fp_type="gt", ignore_background=True):
    # img/zh_val_0.jpg        {
    #     "height": 3508,
    #     "width": 2480,
    #     "ocr_info": [
    #         {"text": "Maribyrnong", "label": "other", "bbox": [1958, 144, 2184, 198]},
    #         {"text": "CITYCOUNCIL", "label": "other", "bbox": [2052, 183, 2171, 214]},
    #     ]
    assert fp_type in ["gt", "pred"]
    key = "label" if fp_type == "gt" else "pred"
    res_dict = dict()
    with open(fp, "r", encoding="utf-8") as fin:
        lines = fin.readlines()

    for _, line in enumerate(lines):
        img_path, info = line.strip().split("\t")
        # get key
        image_name = os.path.basename(img_path)
        res_dict[image_name] = []
        # get infos
        json_info = json.loads(info)
        for single_ocr_info in json_info["ocr_info"]:
            label = single_ocr_info[key].upper()
            if label in ["O", "OTHERS", "OTHER"]:
                label = "O"
            if ignore_background and label == "O":
                continue
            single_ocr_info["label"] = label
            res_dict[image_name].append(copy.deepcopy(single_ocr_info))
    return res_dict