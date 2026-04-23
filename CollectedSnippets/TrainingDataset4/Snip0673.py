def __init__(self, img, dst_width: int, dst_height: int):
    if dst_width < 0 or dst_height < 0:
        raise ValueError("Destination width/height should be > 0")

    self.img = img
    self.src_w = img.shape[1]
    self.src_h = img.shape[0]
    self.dst_w = dst_width
    self.dst_h = dst_height

    self.ratio_x = self.src_w / self.dst_w
    self.ratio_y = self.src_h / self.dst_h

    self.output = self.output_img = (
        np.ones((self.dst_h, self.dst_w, 3), np.uint8) * 255
    )
