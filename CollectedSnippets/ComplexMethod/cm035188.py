def main():
    global_config = config["Global"]

    # build model
    model = build_model(config["Architecture"])

    load_model(config, model)

    # build post process
    post_process_class = build_post_process(config["PostProcess"], global_config)

    # create data ops
    transforms = []
    for op in config["Eval"]["dataset"]["transforms"]:
        op_name = list(op)[0]
        if "Label" in op_name:
            continue
        elif op_name == "KeepKeys":
            op[op_name]["keep_keys"] = ["image", "shape"]
        transforms.append(op)

    ops = create_operators(transforms, global_config)

    save_res_path = config["Global"]["save_res_path"]
    if not os.path.exists(os.path.dirname(save_res_path)):
        os.makedirs(os.path.dirname(save_res_path))

    model.eval()
    with open(save_res_path, "wb") as fout:
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
            post_result = post_process_class(preds, shape_list)
            points, strs = post_result["points"], post_result["texts"]
            # write result
            dt_boxes_json = []
            for poly, str in zip(points, strs):
                tmp_json = {"transcription": str}
                tmp_json["points"] = poly.tolist()
                dt_boxes_json.append(tmp_json)
            otstr = file + "\t" + json.dumps(dt_boxes_json) + "\n"
            fout.write(otstr.encode())
            src_img = cv2.imread(file)
            if global_config["infer_visual_type"] == "EN":
                draw_e2e_res(points, strs, config, src_img, file)
            elif global_config["infer_visual_type"] == "CN":
                src_img = Image.fromarray(cv2.cvtColor(src_img, cv2.COLOR_BGR2RGB))
                draw_e2e_res_for_chinese(
                    src_img,
                    points,
                    strs,
                    config,
                    file,
                    font_path="./doc/fonts/simfang.ttf",
                )

    logger.info("success!")