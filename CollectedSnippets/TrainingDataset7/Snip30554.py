def test_q_annotation(self):
        query = Query(None)
        check = ExpressionWrapper(
            Q(RawSQL("%s = 1", (1,), BooleanField())) | Q(Exists(Item.objects.all())),
            BooleanField(),
        )
        query.add_annotation(check, "_check")
        result = query.get_compiler(using=DEFAULT_DB_ALIAS).execute_sql(SINGLE)
        self.assertEqual(result[0], 1)