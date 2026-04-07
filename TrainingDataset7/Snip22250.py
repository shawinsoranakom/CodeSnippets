def test_dumpdata_uses_default_manager(self):
        """
        Regression for #11286
        Dumpdata honors the default manager. Dump the current contents of
        the database as a JSON fixture
        """
        management.call_command(
            "loaddata",
            "animal.xml",
            verbosity=0,
        )
        management.call_command(
            "loaddata",
            "sequence.json",
            verbosity=0,
        )
        animal = Animal(
            name="Platypus",
            latin_name="Ornithorhynchus anatinus",
            count=2,
            weight=2.2,
        )
        animal.save()

        out = StringIO()
        management.call_command(
            "dumpdata",
            "fixtures_regress.animal",
            format="json",
            stdout=out,
        )

        # Output order isn't guaranteed, so check for parts
        data = out.getvalue()
        animals_data = sorted(
            [
                {
                    "pk": 1,
                    "model": "fixtures_regress.animal",
                    "fields": {
                        "count": 3,
                        "weight": 1.2,
                        "name": "Lion",
                        "latin_name": "Panthera leo",
                    },
                },
                {
                    "pk": 10,
                    "model": "fixtures_regress.animal",
                    "fields": {
                        "count": 42,
                        "weight": 1.2,
                        "name": "Emu",
                        "latin_name": "Dromaius novaehollandiae",
                    },
                },
                {
                    "pk": animal.pk,
                    "model": "fixtures_regress.animal",
                    "fields": {
                        "count": 2,
                        "weight": 2.2,
                        "name": "Platypus",
                        "latin_name": "Ornithorhynchus anatinus",
                    },
                },
            ],
            key=lambda x: x["pk"],
        )

        data = sorted(json.loads(data), key=lambda x: x["pk"])

        self.maxDiff = 1024
        self.assertEqual(data, animals_data)