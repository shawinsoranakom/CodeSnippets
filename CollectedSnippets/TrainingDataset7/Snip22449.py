def test_batch_create_foreign_object(self):
        objs = [
            Person(name="abcd_%s" % i, person_country=self.usa) for i in range(0, 5)
        ]
        Person.objects.bulk_create(objs, 10)