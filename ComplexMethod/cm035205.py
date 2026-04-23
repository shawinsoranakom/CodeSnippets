def main(args):
    image_file_list = get_image_file_list(args.image_dir)
    text_recognizer = TextSR(args)
    valid_image_file_list = []
    img_list = []

    # warmup 2 times
    if args.warmup:
        img = np.random.uniform(0, 255, [16, 64, 3]).astype(np.uint8)
        for i in range(2):
            res = text_recognizer([img] * int(args.sr_batch_num))

    for image_file in image_file_list:
        img, flag, _ = check_and_read(image_file)
        if not flag:
            img = Image.open(image_file).convert("RGB")
        if img is None:
            logger.info("error in loading image:{}".format(image_file))
            continue
        valid_image_file_list.append(image_file)
        img_list.append(img)
    try:
        preds, _ = text_recognizer(img_list)
        for beg_no in range(len(preds)):
            sr_img = preds[beg_no][1]
            lr_img = preds[beg_no][0]
            for i in range(sr_img.shape[0]):
                fm_sr = (sr_img[i] * 255).transpose(1, 2, 0).astype(np.uint8)
                fm_lr = (lr_img[i] * 255).transpose(1, 2, 0).astype(np.uint8)
                img_name_pure = os.path.split(
                    valid_image_file_list[beg_no * args.sr_batch_num + i]
                )[-1]
                cv2.imwrite(
                    "infer_result/sr_{}".format(img_name_pure), fm_sr[:, :, ::-1]
                )
                logger.info(
                    "The visualized image saved in infer_result/sr_{}".format(
                        img_name_pure
                    )
                )

    except Exception as E:
        logger.info(traceback.format_exc())
        logger.info(E)
        exit()
    if args.benchmark:
        text_recognizer.autolog.report()