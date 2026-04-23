def main(args):
    image_file_list = get_image_file_list(args.image_dir)
    valid_image_file_list = []
    img_list = []

    # logger
    log_file = args.save_log_path
    if os.path.isdir(args.save_log_path) or (
        not os.path.exists(args.save_log_path) and args.save_log_path.endswith("/")
    ):
        log_file = os.path.join(log_file, "benchmark_recognition.log")
    logger = get_logger(log_file=log_file)

    # create text recognizer
    text_recognizer = TextRecognizer(args)

    logger.info(
        "In PP-OCRv3, rec_image_shape parameter defaults to '3, 48, 320', "
        "if you are using recognition model with PP-OCRv2 or an older version, please set --rec_image_shape='3,32,320"
    )

    # warmup 2 times
    if args.warmup:
        img = np.random.uniform(0, 255, [48, 320, 3]).astype(np.uint8)
        for i in range(2):
            res = text_recognizer([img] * int(args.rec_batch_num))

    for image_file in image_file_list:
        img, flag, _ = check_and_read(image_file)
        if not flag:
            img = cv2.imread(image_file)
        if img is None:
            logger.info("error in loading image:{}".format(image_file))
            continue
        valid_image_file_list.append(image_file)
        img_list.append(img)
    try:
        rec_res, _ = text_recognizer(img_list)

    except Exception as E:
        logger.info(traceback.format_exc())
        logger.info(E)
        exit()
    for ino in range(len(img_list)):
        logger.info(
            "Predicts of {}:{}".format(valid_image_file_list[ino], rec_res[ino])
        )
    if args.benchmark:
        text_recognizer.autolog.report()