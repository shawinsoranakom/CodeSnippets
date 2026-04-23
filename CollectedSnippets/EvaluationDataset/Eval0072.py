def main() -> None:

    img_paths, annos = get_dataset(LABEL_DIR, IMG_DIR)
    for index in range(NUMBER_IMAGES):
        idxs = random.sample(range(len(annos)), 4)
        new_image, new_annos, path = update_image_and_anno(
            img_paths,
            annos,
            idxs,
            OUTPUT_SIZE,
            SCALE_RANGE,
            filter_scale=FILTER_TINY_SCALE,
        )

        letter_code = random_chars(32)
        file_name = path.split(os.sep)[-1].rsplit(".", 1)[0]
        file_root = f"{OUTPUT_DIR}/{file_name}_MOSAIC_{letter_code}"
        cv2.imwrite(f"{file_root}.jpg", new_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f"Succeeded {index + 1}/{NUMBER_IMAGES} with {file_name}")
        annos_list = []
        for anno in new_annos:
            width = anno[3] - anno[1]
            height = anno[4] - anno[2]
            x_center = anno[1] + width / 2
            y_center = anno[2] + height / 2
            obj = f"{anno[0]} {x_center} {y_center} {width} {height}"
            annos_list.append(obj)
        with open(f"{file_root}.txt", "w") as outfile:
            outfile.write("\n".join(line for line in annos_list))
