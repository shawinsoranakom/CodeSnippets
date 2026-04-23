def inherited_compare(testcase, pk, klass, data):
    instance = klass.objects.get(id=pk)
    for key, value in data.items():
        testcase.assertEqual(value, getattr(instance, key))