def fk_compare(testcase, pk, klass, data):
    instance = klass.objects.get(id=pk)
    testcase.assertEqual(data, instance.data_id)