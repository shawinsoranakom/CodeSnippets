def test_extraneous_query_is_not_run(self):
        Formset = modelformset_factory(Network, fields="__all__")
        data = {
            "test-TOTAL_FORMS": "1",
            "test-INITIAL_FORMS": "0",
            "test-MAX_NUM_FORMS": "",
            "test-0-name": "Random Place",
        }
        with self.assertNumQueries(1):
            formset = Formset(data, prefix="test")
            formset.save()