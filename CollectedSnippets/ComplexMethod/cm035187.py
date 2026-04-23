def main(args):
    image_file_list = get_image_file_list(args.image_dir)
    is_visualize = False
    headers = {"Content-type": "application/json"}
    cnt = 0
    total_time = 0
    for image_file in image_file_list:
        img = open(image_file, "rb").read()
        if img is None:
            logger.info("error in loading image:{}".format(image_file))
            continue
        img_name = os.path.basename(image_file)
        # seed http request
        starttime = time.time()
        data = {"images": [cv2_to_base64(img)]}
        r = requests.post(url=args.server_url, headers=headers, data=json.dumps(data))
        elapse = time.time() - starttime
        total_time += elapse
        logger.info("Predict time of %s: %.3fs" % (image_file, elapse))
        res = r.json()["results"][0]
        logger.info(res)

        if args.visualize:
            draw_img = None
            if "structure_table" in args.server_url:
                to_excel(res["html"], "./{}.xlsx".format(img_name))
            elif "structure_system" in args.server_url:
                save_structure_res(res["regions"], args.output, image_file)
            else:
                draw_img = draw_server_result(image_file, res)
            if draw_img is not None:
                if not os.path.exists(args.output):
                    os.makedirs(args.output)
                cv2.imwrite(
                    os.path.join(args.output, os.path.basename(image_file)),
                    draw_img[:, :, ::-1],
                )
                logger.info(
                    "The visualized image saved in {}".format(
                        os.path.join(args.output, os.path.basename(image_file))
                    )
                )
        cnt += 1
        if cnt % 100 == 0:
            logger.info("{} processed".format(cnt))
    logger.info("avg time cost: {}".format(float(total_time) / cnt))