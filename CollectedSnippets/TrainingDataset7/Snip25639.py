def test_db_do_nothing_chain(self):
        class GrandParent(models.Model):
            pass

        class Parent(models.Model):
            grand_parent = models.ForeignKey(GrandParent, models.DO_NOTHING)

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.DB_SET_NULL, null=True)

        field = Child._meta.get_field("parent")
        self.assertEqual(field.check(databases=self.databases), [])