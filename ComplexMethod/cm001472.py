def process(self, pp: scripts_postprocessing.PostprocessedImage, enable, split_threshold, overlap_ratio):
        if not enable:
            return

        width = pp.shared.target_width
        height = pp.shared.target_height

        if not width or not height:
            return

        if pp.image.height > pp.image.width:
            ratio = (pp.image.width * height) / (pp.image.height * width)
            inverse_xy = False
        else:
            ratio = (pp.image.height * width) / (pp.image.width * height)
            inverse_xy = True

        if ratio >= 1.0 or ratio > split_threshold:
            return

        result, *others = split_pic(pp.image, inverse_xy, width, height, overlap_ratio)

        pp.image = result
        pp.extra_images = [pp.create_copy(x) for x in others]