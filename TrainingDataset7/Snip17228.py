def test_set_returning_functions(self):
        class JSONBPathQuery(Func):
            function = "jsonb_path_query"
            output_field = JSONField()
            set_returning = True

        test_model = JsonModel.objects.create(
            data={"key": [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]}, id=1
        )
        qs = JsonModel.objects.annotate(
            table_element=JSONBPathQuery("data", Value("$.key[*]"))
        ).filter(pk=test_model.pk)

        self.assertEqual(qs.count(), len(qs))