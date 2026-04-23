def test_do_nothing_db_chain(self):
        class GrandParent(models.Model):
            pass

        class Parent(models.Model):
            grand_parent = models.ForeignKey(GrandParent, models.DB_SET_NULL, null=True)

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.DO_NOTHING)

        field = Child._meta.get_field("parent")
        self.assertEqual(field.check(databases=self.databases), [])