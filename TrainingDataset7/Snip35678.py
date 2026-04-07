def test_update_pk_field(self):
        person_boss = Person.objects.create(name="Boss", gender="F")
        with self.assertRaisesMessage(ValueError, self.msg % "id"):
            person_boss.save(update_fields=["id"])