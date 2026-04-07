def test_initially_deferred_database_constraint(self):
        obj_1 = UniqueConstraintDeferrable.objects.create(name="p1", shelf="front")
        obj_2 = UniqueConstraintDeferrable.objects.create(name="p2", shelf="back")

        def swap():
            obj_1.name, obj_2.name = obj_2.name, obj_1.name
            obj_1.save()
            obj_2.save()

        swap()
        # Behavior can be changed with SET CONSTRAINTS.
        with self.assertRaises(IntegrityError):
            with atomic(), connection.cursor() as cursor:
                constraint_name = connection.ops.quote_name("name_init_deferred_uniq")
                cursor.execute("SET CONSTRAINTS %s IMMEDIATE" % constraint_name)
                swap()