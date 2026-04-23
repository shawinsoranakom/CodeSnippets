def get_dataset(label_dir: str, img_dir: str) -> tuple[list, list]:
    img_paths = []
    labels = []
    for label_file in glob.glob(os.path.join(label_dir, "*.txt")):
        label_name = label_file.split(os.sep)[-1].rsplit(".", 1)[0]
        with open(label_file) as in_file:
            obj_lists = in_file.readlines()
        img_path = os.path.join(img_dir, f"{label_name}.jpg")

        boxes = []
        for obj_list in obj_lists:
            obj = obj_list.rstrip("\n").split(" ")
            boxes.append(
                [
                    int(obj[0]),
                    float(obj[1]),
                    float(obj[2]),
                    float(obj[3]),
                    float(obj[4]),
                ]
            )
        if not boxes:
            continue
        img_paths.append(img_path)
        labels.append(boxes)
    return img_paths, labels
