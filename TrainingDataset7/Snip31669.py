def generic_compare(testcase, pk, klass, data):
    instance = klass.objects.get(id=pk)
    testcase.assertEqual(data[0], instance.data)
    testcase.assertEqual(data[1:], [t.data for t in instance.tags.order_by("id")])