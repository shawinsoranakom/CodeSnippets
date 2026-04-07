def test_composite_pk_must_be_unique_strings(self):
        test_cases = (
            (),
            (0,),
            (1,),
            ("id", False),
            ("id", "id"),
            (("id",),),
        )

        for i, args in enumerate(test_cases):
            with (
                self.subTest(args=args),
                self.assertRaisesMessage(
                    ValueError, "CompositePrimaryKey args must be unique strings."
                ),
            ):
                models.CompositePrimaryKey(*args)