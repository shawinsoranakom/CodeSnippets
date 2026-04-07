def test_update_inherited_pk_field(self):
        employee_boss = Employee.objects.create(name="Boss", gender="F")
        with self.assertRaisesMessage(ValueError, self.msg % "id"):
            employee_boss.save(update_fields=["id"])