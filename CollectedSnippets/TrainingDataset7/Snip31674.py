def o2o_compare(testcase, pk, klass, data):
    instance = klass.objects.get(data=data)
    testcase.assertEqual(data, instance.data_id)