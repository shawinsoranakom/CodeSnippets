def test_hash_nested(self):
        error_dict = {
            "field1": ValidationError(
                "error %(parm1)s %(parm2)s",
                code="my_code",
                params={"parm2": "val2", "parm1": "val1"},
            ),
            "field2": "other",
        }
        error = ValidationError(error_dict)
        self.assertEqual(hash(error), hash(ValidationError(dict(error_dict))))
        self.assertEqual(
            hash(error),
            hash(
                ValidationError(
                    {
                        "field1": ValidationError(
                            "error %(parm1)s %(parm2)s",
                            code="my_code",
                            params={"parm1": "val1", "parm2": "val2"},
                        ),
                        "field2": "other",
                    }
                )
            ),
        )
        self.assertNotEqual(
            hash(error),
            hash(
                ValidationError(
                    {**error_dict, "field2": "message"},
                )
            ),
        )
        self.assertNotEqual(
            hash(error),
            hash(
                ValidationError(
                    {
                        "field1": ValidationError(
                            "error %(parm1)s val2",
                            code="my_code",
                            params={"parm1": "val1"},
                        ),
                        "field2": "other",
                    }
                )
            ),
        )