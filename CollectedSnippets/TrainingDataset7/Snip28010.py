def test_ordering_by_transform(self):
        mariadb = connection.vendor == "mysql" and connection.mysql_is_mariadb
        values = [
            {"ord": 93, "name": "bar"},
            {"ord": 22.1, "name": "foo"},
            {"ord": -1, "name": "baz"},
            {"ord": 21.931902, "name": "spam"},
            {"ord": -100291029, "name": "eggs"},
        ]
        for field_name in ["value", "value_custom"]:
            with self.subTest(field=field_name):
                objs = [
                    NullableJSONModel.objects.create(**{field_name: value})
                    for value in values
                ]
                query = NullableJSONModel.objects.filter(
                    **{"%s__name__isnull" % field_name: False},
                ).order_by("%s__ord" % field_name)
                expected = [objs[4], objs[2], objs[3], objs[1], objs[0]]
                if mariadb or connection.vendor == "oracle":
                    # MariaDB and Oracle return JSON values as strings.
                    expected = [objs[2], objs[4], objs[3], objs[1], objs[0]]
                self.assertSequenceEqual(query, expected)