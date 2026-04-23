def test_hash(self):
        error1 = ValidationError("message")
        error2 = ValidationError("message", code="my_code1")
        error3 = ValidationError("message", code="my_code2")
        error4 = ValidationError(
            "error %(parm1)s %(parm2)s",
            code="my_code1",
            params={"parm1": "val1", "parm2": "val2"},
        )
        error5 = ValidationError({"field1": "message", "field2": "other"})
        error6 = ValidationError({"field1": "message"})
        error7 = ValidationError(
            [
                ValidationError({"field1": "field error", "field2": "other"}),
                "message",
            ]
        )

        self.assertEqual(hash(error1), hash(ValidationError("message")))
        self.assertNotEqual(hash(error1), hash(ValidationError("message2")))
        self.assertNotEqual(hash(error1), hash(error2))
        self.assertNotEqual(hash(error1), hash(error4))
        self.assertNotEqual(hash(error1), hash(error5))
        self.assertNotEqual(hash(error1), hash(error6))
        self.assertNotEqual(hash(error1), hash(error7))
        self.assertEqual(
            hash(error2),
            hash(ValidationError("message", code="my_code1")),
        )
        self.assertNotEqual(
            hash(error2),
            hash(ValidationError("other", code="my_code1")),
        )
        self.assertNotEqual(hash(error2), hash(error3))
        self.assertNotEqual(hash(error2), hash(error4))
        self.assertNotEqual(hash(error2), hash(error5))
        self.assertNotEqual(hash(error2), hash(error6))
        self.assertNotEqual(hash(error2), hash(error7))

        self.assertEqual(
            hash(error4),
            hash(
                ValidationError(
                    "error %(parm1)s %(parm2)s",
                    code="my_code1",
                    params={"parm1": "val1", "parm2": "val2"},
                )
            ),
        )
        self.assertNotEqual(
            hash(error4),
            hash(
                ValidationError(
                    "error %(parm1)s %(parm2)s",
                    code="my_code2",
                    params={"parm1": "val1", "parm2": "val2"},
                )
            ),
        )
        self.assertNotEqual(
            hash(error4),
            hash(
                ValidationError(
                    "error %(parm1)s %(parm2)s",
                    code="my_code1",
                    params={"parm2": "val2"},
                )
            ),
        )
        self.assertNotEqual(
            hash(error4),
            hash(
                ValidationError(
                    "error %(parm1)s %(parm2)s",
                    code="my_code1",
                    params={"parm2": "val1", "parm1": "val2"},
                )
            ),
        )
        self.assertNotEqual(
            hash(error4),
            hash(
                ValidationError(
                    "error val1 val2",
                    code="my_code1",
                )
            ),
        )
        # params ordering is ignored.
        self.assertEqual(
            hash(error4),
            hash(
                ValidationError(
                    "error %(parm1)s %(parm2)s",
                    code="my_code1",
                    params={"parm2": "val2", "parm1": "val1"},
                )
            ),
        )

        self.assertEqual(
            hash(error5),
            hash(ValidationError({"field1": "message", "field2": "other"})),
        )
        self.assertNotEqual(
            hash(error5),
            hash(ValidationError({"field1": "message", "field2": "other2"})),
        )
        self.assertNotEqual(
            hash(error5),
            hash(ValidationError({"field1": "message", "field3": "other"})),
        )
        self.assertNotEqual(error5, error6)
        # fields ordering is ignored.
        self.assertEqual(
            hash(error5),
            hash(ValidationError({"field2": "other", "field1": "message"})),
        )

        self.assertNotEqual(
            hash(error7),
            hash(ValidationError(error7.error_list[1:])),
        )
        self.assertNotEqual(
            hash(ValidationError(["message"])),
            hash(ValidationError([ValidationError("message", code="my_code")])),
        )
        # messages ordering is ignored.
        self.assertEqual(
            hash(error7),
            hash(ValidationError(list(reversed(error7.error_list)))),
        )

        self.assertNotEqual(hash(error4), hash(ValidationError([error4])))
        self.assertNotEqual(hash(ValidationError([error4])), hash(error4))
        self.assertNotEqual(
            hash(error4),
            hash(ValidationError({"field1": error4})),
        )