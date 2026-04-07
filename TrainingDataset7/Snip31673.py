def im_compare(testcase, pk, klass, data):
    instance = klass.objects.get(id=pk)
    testcase.assertEqual(data["left"], instance.left_id)
    testcase.assertEqual(data["right"], instance.right_id)
    if "extra" in data:
        testcase.assertEqual(data["extra"], instance.extra)
    else:
        testcase.assertEqual("doesn't matter", instance.extra)