def test_abstract_parent_link(self):
        class A(models.Model):
            pass

        class B(A):
            a = models.OneToOneField("A", parent_link=True, on_delete=models.CASCADE)

            class Meta:
                abstract = True

        class C(B):
            pass

        self.assertIs(C._meta.parents[A], C._meta.get_field("a"))