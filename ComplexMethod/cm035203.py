def minmax_size_(
        self,
        img,
        max_dimensions,
        min_dimensions,
    ):
        if max_dimensions is not None:
            ratios = [a / b for a, b in zip(img.size, max_dimensions)]
            if any([r > 1 for r in ratios]):
                size = np.array(img.size) // max(ratios)
                img = img.resize(tuple(size.astype(int)), Image.BILINEAR)
        if min_dimensions is not None:
            # hypothesis: there is a dim in img smaller than min_dimensions, and return a proper dim >= min_dimensions
            padded_size = [
                max(img_dim, min_dim)
                for img_dim, min_dim in zip(img.size, min_dimensions)
            ]
            if padded_size != list(img.size):  # assert hypothesis
                padded_im = Image.new("L", padded_size, 255)
                padded_im.paste(img, img.getbbox())
                img = padded_im
        return img