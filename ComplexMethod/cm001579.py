def upscale(self, img: PIL.Image, scale, selected_model: str = None):
        self.scale = scale
        dest_w = int((img.width * scale) // 8 * 8)
        dest_h = int((img.height * scale) // 8 * 8)

        for i in range(3):
            if img.width >= dest_w and img.height >= dest_h and (i > 0 or scale != 1):
                break

            if shared.state.interrupted:
                break

            shape = (img.width, img.height)

            img = self.do_upscale(img, selected_model)

            if shape == (img.width, img.height):
                break

        if img.width != dest_w or img.height != dest_h:
            img = img.resize((int(dest_w), int(dest_h)), resample=LANCZOS)

        return img