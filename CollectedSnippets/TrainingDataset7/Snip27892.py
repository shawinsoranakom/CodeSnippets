def test_to_python(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            fk = models.ForeignKey(Foo, models.CASCADE)

        self.assertEqual(Bar._meta.get_field("fk").to_python("1"), 1)