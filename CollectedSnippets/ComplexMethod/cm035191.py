def main():
    global_config = config["Global"]

    # build model
    model = build_model(config["Architecture"])

    load_model(config, model)
    # build post process
    post_process_class = build_post_process(config["PostProcess"])

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

            src_img = cv2.imread(file)

            dt_boxes_json = []
            # parser boxes if post_result is dict
            if isinstance(post_result, dict):
                det_box_json = {}
                for k in post_result.keys():
                    boxes = post_result[k][0]["points"]
                    dt_boxes_list = []
                    for box in boxes:
                        tmp_json = {"transcription": ""}
                        tmp_json["points"] = np.array(box).tolist()
                        dt_boxes_list.append(tmp_json)
                    det_box_json[k] = dt_boxes_list
                    save_det_path = os.path.dirname(
                        config["Global"]["save_res_path"]
                    ) + "/det_results_{}/".format(k)
                    draw_det_res(boxes, config, src_img, file, save_det_path)
            else:
                boxes = post_result[0]["points"]
                dt_boxes_json = []
                # write result
                for box in boxes:
                    tmp_json = {"transcription": ""}
                    tmp_json["points"] = np.array(box).tolist()
                    dt_boxes_json.append(tmp_json)
                save_det_path = (
                    os.path.dirname(config["Global"]["save_res_path"]) + "/det_results/"
                )
                draw_det_res(boxes, config, src_img, file, save_det_path)
            otstr = file + "\t" + json.dumps(dt_boxes_json) + "\n"
            fout.write(otstr.encode())

    logger.info("success!")