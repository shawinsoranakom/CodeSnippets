def test_dumps_loads(self):
        "dumps and loads be reversible for any JSON serializable object"
        objects = [
            ["a", "list"],
            "a string \u2019",
            {"a": "dictionary"},
        ]
        for o in objects:
            self.assertNotEqual(o, signing.dumps(o))
            self.assertEqual(o, signing.loads(signing.dumps(o)))
            self.assertNotEqual(o, signing.dumps(o, compress=True))
            self.assertEqual(o, signing.loads(signing.dumps(o, compress=True)))