def test_truncate_complex(self):
        self.assertEqual(
            truncatewords_html(
                "<i>Buenos d&iacute;as! &#x00bf;C&oacute;mo est&aacute;?</i>", 3
            ),
            "<i>Buenos días! ¿Cómo …</i>",
        )