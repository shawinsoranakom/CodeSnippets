def test_clean_paragraphs(self):
        # from https://www.lipsum.com/
        input = textwrap.dedent(
            """
            Lorem              ipsum dolor sit amet,
            consectetur adipiscing elit.

               Curabitur ac fermentum eros.

            Maecenas                   libero est,
                    ultricies
            eget ligula eget,    """
        )

        truth = [
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "Curabitur ac fermentum eros.",
            "Maecenas libero est, ultricies eget ligula eget,",
        ]

        result = config_util._clean_paragraphs(input)
        self.assertEqual(truth, result)