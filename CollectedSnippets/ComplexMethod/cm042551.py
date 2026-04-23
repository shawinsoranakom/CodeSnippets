def test_convert_image(self):
        SIZE = (100, 100)
        # straight forward case: RGB and JPEG
        COLOUR = (0, 127, 255)
        im, buf = _create_image("JPEG", "RGB", SIZE, COLOUR)
        converted, converted_buf = self.pipeline.convert_image(im, response_body=buf)
        assert converted.mode == "RGB"
        assert converted.getcolors() == [(10000, COLOUR)]
        # check that we don't convert JPEGs again
        assert converted_buf == buf

        # check that thumbnail keep image ratio
        thumbnail, _ = self.pipeline.convert_image(
            converted, size=(10, 25), response_body=converted_buf
        )
        assert thumbnail.mode == "RGB"
        assert thumbnail.size == (10, 10)

        # transparency case: RGBA and PNG
        COLOUR = (0, 127, 255, 50)
        im, buf = _create_image("PNG", "RGBA", SIZE, COLOUR)
        converted, _ = self.pipeline.convert_image(im, response_body=buf)
        assert converted.mode == "RGB"
        assert converted.getcolors() == [(10000, (205, 230, 255))]

        # transparency case with palette: P and PNG
        COLOUR = (0, 127, 255, 50)
        im, buf = _create_image("PNG", "RGBA", SIZE, COLOUR)
        im = im.convert("P")
        converted, _ = self.pipeline.convert_image(im, response_body=buf)
        assert converted.mode == "RGB"
        assert converted.getcolors() == [(10000, (205, 230, 255))]