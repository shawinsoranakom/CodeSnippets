def test_serialize_non_identifier_keyword_args(self):
        instance = DeconstructibleArbitrary(
            **{"kebab-case": 1, "my_list": [1, 2, 3], "123foo": {"456bar": set()}},
            regular="kebab-case",
            **{"simple": 1, "complex": 3.1416},
        )
        string, imports = MigrationWriter.serialize(instance)
        self.assertEqual(
            string,
            "migrations.test_writer.DeconstructibleArbitrary(complex=3.1416, "
            "my_list=[1, 2, 3], regular='kebab-case', simple=1, "
            "**{'123foo': {'456bar': set()}, 'kebab-case': 1})",
        )
        self.assertEqual(imports, {"import migrations.test_writer"})
        result = self.serialize_round_trip(instance)
        self.assertEqual(result.args, instance.args)
        self.assertEqual(result.kwargs, instance.kwargs)