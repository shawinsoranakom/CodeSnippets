def main(args):
    image_file_list = get_image_file_list(args.image_dir)
    image_file_list = image_file_list
    image_file_list = image_file_list[args.process_id :: args.total_process_num]

    if not args.use_pdf2docx_api:
        structure_sys = StructureSystem(args)
        save_folder = os.path.join(args.output, structure_sys.mode)
        os.makedirs(save_folder, exist_ok=True)
    img_num = len(image_file_list)

    for i, image_file in enumerate(image_file_list):
        logger.info("[{}/{}] {}".format(i, img_num, image_file))
        img, flag_gif, flag_pdf = check_and_read(image_file)
        img_name = os.path.basename(image_file).split(".")[0]

        if args.recovery and args.use_pdf2docx_api and flag_pdf:
            try_import("pdf2docx")
            from pdf2docx.converter import Converter

            os.makedirs(args.output, exist_ok=True)
            docx_file = os.path.join(args.output, "{}_api.docx".format(img_name))
            cv = Converter(image_file)
            cv.convert(docx_file)
            cv.close()
            logger.info("docx save to {}".format(docx_file))
            continue

        if not flag_gif and not flag_pdf:
            img = cv2.imread(image_file)

        if not flag_pdf:
            if img is None:
                logger.error("error in loading image:{}".format(image_file))
                continue
            imgs = [img]
        else:
            imgs = img

        all_res = []
        for index, img in enumerate(imgs):
            res, time_dict = structure_sys(img, img_idx=index)
            img_save_path = os.path.join(
                save_folder, img_name, "show_{}.jpg".format(index)
            )
            os.makedirs(os.path.join(save_folder, img_name), exist_ok=True)
            if structure_sys.mode == "structure" and res != []:
                draw_img = draw_structure_result(img, res, args.vis_font_path)
                save_structure_res(res, save_folder, img_name, index)
            elif structure_sys.mode == "kie":
                if structure_sys.kie_predictor.predictor is not None:
                    draw_img = draw_re_results(img, res, font_path=args.vis_font_path)
                else:
                    draw_img = draw_ser_results(img, res, font_path=args.vis_font_path)

                with open(
                    os.path.join(save_folder, img_name, "res_{}_kie.txt".format(index)),
                    "w",
                    encoding="utf8",
                ) as f:
                    res_str = "{}\t{}\n".format(
                        image_file, json.dumps({"ocr_info": res}, ensure_ascii=False)
                    )
                    f.write(res_str)
            if res != []:
                cv2.imwrite(img_save_path, draw_img)
                logger.info("result save to {}".format(img_save_path))
            if args.recovery and res != []:
                from ppstructure.recovery.recovery_to_doc import (
                    sorted_layout_boxes,
                    convert_info_docx,
                )
                from ppstructure.recovery.recovery_to_markdown import (
                    convert_info_markdown,
                )

                h, w, _ = img.shape
                res = sorted_layout_boxes(res, w)
                all_res += res

        if args.recovery and all_res != []:
            try:
                convert_info_docx(img, all_res, save_folder, img_name)
                if args.recovery_to_markdown:
                    convert_info_markdown(all_res, save_folder, img_name)
            except Exception as ex:
                logger.error(
                    "error in layout recovery image:{}, err msg: {}".format(
                        image_file, ex
                    )
                )
                continue
        logger.info("Predict time : {:.3f}s".format(time_dict["all"]))