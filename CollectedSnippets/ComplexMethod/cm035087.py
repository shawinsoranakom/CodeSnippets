def txt2pickle(images, equations, save_dir):
    imagesize = try_import("imagesize")
    save_p = os.path.join(save_dir, "latexocr_{}.pkl".format(images.split("/")[-1]))
    min_dimensions = (32, 32)
    max_dimensions = (672, 192)
    max_length = 512
    data = defaultdict(lambda: [])
    if images is not None and equations is not None:
        images_list = [
            path.replace("\\", "/") for path in glob.glob(join(images, "*.png"))
        ]
        indices = [int(os.path.basename(img).split(".")[0]) for img in images_list]
        eqs = open(equations, "r").read().split("\n")
        for i, im in tqdm(enumerate(images_list), total=len(images_list)):
            width, height = imagesize.get(im)
            if (
                min_dimensions[0] <= width <= max_dimensions[0]
                and min_dimensions[1] <= height <= max_dimensions[1]
            ):
                divide_h = math.ceil(height / 16) * 16
                divide_w = math.ceil(width / 16) * 16
                im = os.path.basename(im)
                data[(divide_w, divide_h)].append((eqs[indices[i]], im))
        data = dict(data)
        with open(save_p, "wb") as file:
            pickle.dump(data, file)