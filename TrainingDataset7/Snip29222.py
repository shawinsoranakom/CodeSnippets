def test_foreign_key_relation(self):
        person = Person(name="Someone")
        pet = Pet()
        with self.assertRaisesMessage(ValueError, self.router_prevents_msg):
            pet.owner = person