def test_render_context(self):
        test_context = RenderContext({"fruit": "papaya"})

        # push() limits access to the topmost dict
        test_context.push()

        test_context["vegetable"] = "artichoke"
        self.assertEqual(list(test_context), ["vegetable"])

        self.assertNotIn("fruit", test_context)
        with self.assertRaises(KeyError):
            test_context["fruit"]
        self.assertIsNone(test_context.get("fruit"))