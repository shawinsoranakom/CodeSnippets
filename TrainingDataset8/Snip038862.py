def test_marshall_svg(self, image_markup: str, expected_prefix: str):
        image_list_proto = ImageListProto()
        image.marshall_images(
            None,
            image_markup,
            None,
            0,
            image_list_proto,
            False,
        )
        img = image_list_proto.imgs[0]
        self.assertTrue(img.markup.startswith(expected_prefix))