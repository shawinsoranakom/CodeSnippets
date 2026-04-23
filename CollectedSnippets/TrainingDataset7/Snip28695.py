def test_set_name(self):
        class ClassAttr:
            called = None

            def __set_name__(self_, owner, name):
                self.assertIsNone(self_.called)
                self_.called = (owner, name)

        class A(models.Model):
            attr = ClassAttr()

        self.assertEqual(A.attr.called, (A, "attr"))