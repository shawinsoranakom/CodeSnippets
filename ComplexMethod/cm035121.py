def main(args):
    image_file_list = get_image_file_list(args.image_dir)
    table_structurer = TableStructurer(args)
    count = 0
    total_time = 0
    os.makedirs(args.output, exist_ok=True)
    with open(
        os.path.join(args.output, "infer.txt"), mode="w", encoding="utf-8"
    ) as f_w:
        for image_file in image_file_list:
            img, flag, _ = check_and_read(image_file)
            if not flag:
                img = cv2.imread(image_file)
            if img is None:
                logger.info("error in loading image:{}".format(image_file))
                continue
            structure_res, elapse = table_structurer(img)
            structure_str_list, bbox_list = structure_res
            bbox_list_str = json.dumps(bbox_list.tolist())
            logger.info("result: {}, {}".format(structure_str_list, bbox_list_str))
            f_w.write("result: {}, {}\n".format(structure_str_list, bbox_list_str))

            if len(bbox_list) > 0 and len(bbox_list[0]) == 4:
                img = draw_rectangle(image_file, bbox_list)
            else:
                img = utility.draw_boxes(img, bbox_list)
            img_save_path = os.path.join(args.output, os.path.basename(image_file))
            cv2.imwrite(img_save_path, img)
            logger.info("save vis result to {}".format(img_save_path))
            if count > 0:
                total_time += elapse
            count += 1
            logger.info("Predict time of {}: {}".format(image_file, elapse))
    if args.benchmark:
        table_structurer.autolog.report()