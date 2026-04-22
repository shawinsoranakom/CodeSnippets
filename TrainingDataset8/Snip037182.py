def generate_image_channel_data(self):
        # np.array(image) returns the following shape
        #   (width, height, channels)
        # and
        #   transpose((2, 0, 1)) is really
        #   transpose((channels, width, height))
        # So then we get channels, width, height which makes extracting
        # single channels easier.
        array = np.array(self._image).transpose((2, 0, 1))

        for idx, name in zip(range(0, 4), ["red", "green", "blue", "alpha"]):
            data = io.BytesIO()
            img = Image.fromarray(array[idx].astype(np.uint8))
            img.save(data, format="PNG")
            self._data["%s.png" % name] = data.getvalue()