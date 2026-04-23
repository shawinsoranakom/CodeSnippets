def __call__(self, data):
        img = data["image"]
        assert type(img) is bytes and len(img) > 0, "invalid input 'img' in DecodeImage"
        img = np.frombuffer(img, dtype="uint8")
        if self.img_mode == "GRAY":
            # For GRAY mode, decode directly to a single-channel grayscale image.
            decode_flag = cv2.IMREAD_GRAYSCALE
        else:
            # For RGB mode, decode to a 3-channel color image.
            decode_flag = cv2.IMREAD_COLOR

        if self.ignore_orientation:
            decode_flag |= cv2.IMREAD_IGNORE_ORIENTATION

        img = cv2.imdecode(img, decode_flag)

        if img is None:
            return None
        if self.img_mode == "GRAY":
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif self.img_mode == "RGB":
            assert img.shape[2] == 3, "invalid shape of image[%s]" % (img.shape)
            img = img[:, :, ::-1]

        if self.channel_first:
            img = img.transpose((2, 0, 1))

        data["image"] = img
        return data