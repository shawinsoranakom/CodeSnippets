def main(config, device, logger, vdl_writer):
    global_config = config["Global"]

    # build post process
    post_process_class = build_post_process(config["PostProcess"], global_config)

    # build model
    if hasattr(post_process_class, "character"):
        config["Architecture"]["Head"]["out_channels"] = len(
            getattr(post_process_class, "character")
        )

    model = build_model(config["Architecture"])
    algorithm = config["Architecture"]["algorithm"]

    load_model(config, model)

    # create data ops
    transforms = []
    for op in config["Eval"]["dataset"]["transforms"]:
        op_name = list(op)[0]
        if "Encode" in op_name:
            continue
        if op_name == "KeepKeys":
            op[op_name]["keep_keys"] = ["image", "shape"]
        transforms.append(op)

    global_config["infer_mode"] = True
    ops = create_operators(transforms, global_config)

    save_res_path = config["Global"]["save_res_path"]
    os.makedirs(save_res_path, exist_ok=True)

    model.eval()
    with open(
        os.path.join(save_res_path, "infer.txt"), mode="w", encoding="utf-8"
    ) as f_w:
        for file in get_image_file_list(config["Global"]["infer_img"]):
            logger.info("infer_img: {}".format(file))
            with open(file, "rb") as f:
                img = f.read()
                data = {"image": img}
            batch = transform(data, ops)
            images = np.expand_dims(batch[0], axis=0)
            shape_list = np.expand_dims(batch[1], axis=0)

            images = paddle.to_tensor(images)
            preds = model(images)
            post_result = post_process_class(preds, [shape_list])

            structure_str_list = post_result["structure_batch_list"][0]
            bbox_list = post_result["bbox_batch_list"][0]
            structure_str_list = structure_str_list[0]
            structure_str_list = (
                ["<html>", "<body>", "<table>"]
                + structure_str_list
                + ["</table>", "</body>", "</html>"]
            )
            bbox_list_str = json.dumps(bbox_list.tolist())

            logger.info("result: {}, {}".format(structure_str_list, bbox_list_str))
            f_w.write("result: {}, {}\n".format(structure_str_list, bbox_list_str))

            if len(bbox_list) > 0 and len(bbox_list[0]) == 4:
                img = draw_rectangle(file, bbox_list)
            else:
                img = draw_boxes(cv2.imread(file), bbox_list)
            cv2.imwrite(os.path.join(save_res_path, os.path.basename(file)), img)
            logger.info("save result to {}".format(save_res_path))
        logger.info("success!")