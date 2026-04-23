def test_mark_safe_object_implementing_dunder_str(self):
        class Obj:
            def __str__(self):
                return "<obj>"

        s = mark_safe(Obj())

        self.assertRenderEqual("{{ s }}", "<obj>", s=s)