def setUpTestData(cls):
        cls.primitives = [True, False, "yes", 7, 9.6]
        values = [
            None,
            [],
            {},
            {"a": "b", "c": 14},
            {
                "a": "b",
                "c": 14,
                "d": ["e", {"f": "g"}],
                "h": True,
                "i": False,
                "j": None,
                "k": {"l": "m"},
                "n": [None, True, False],
                "o": '"quoted"',
                "p": 4.2,
                "r": {"s": True, "t": False},
            },
            [1, [2]],
            {"k": True, "l": False, "foo": "bax"},
            {
                "foo": "bar",
                "baz": {"a": "b", "c": "d"},
                "bar": ["foo", "bar"],
                "bax": {"foo": "bar"},
            },
        ]
        objs = [NullableJSONModel(value=value) for value in values]
        if connection.features.supports_primitives_in_json_field:
            objs.extend([NullableJSONModel(value=value) for value in cls.primitives])
        objs = NullableJSONModel.objects.bulk_create(objs)
        # Some backends don't return primary keys after bulk_create.
        if any(obj.pk is None for obj in objs):
            objs = list(NullableJSONModel.objects.order_by("id"))
        cls.objs = objs
        cls.raw_sql = "%s::jsonb" if connection.vendor == "postgresql" else "%s"