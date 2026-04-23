def get_datalist(train_data_path):
    """
    获取训练和验证的数据list
    :param train_data_path: 训练的dataset文件列表，每个文件内以如下格式存储 ‘path/to/img\tlabel’
    :return:
    """
    train_data = []
    for p in train_data_path:
        with open(p, "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip("\n").replace(".jpg ", ".jpg\t").split("\t")
                if len(line) > 1:
                    img_path = pathlib.Path(line[0].strip(" "))
                    label_path = pathlib.Path(line[1].strip(" "))
                    if (
                        img_path.exists()
                        and img_path.stat().st_size > 0
                        and label_path.exists()
                        and label_path.stat().st_size > 0
                    ):
                        train_data.append((str(img_path), str(label_path)))
    return train_data