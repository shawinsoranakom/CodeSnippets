def data_compare(testcase, pk, klass, data):
    instance = klass.objects.get(id=pk)
    if klass == BinaryData and data is not None:
        testcase.assertEqual(
            bytes(data),
            bytes(instance.data),
            "Objects with PK=%s not equal; expected '%s' (%s), got '%s' (%s)"
            % (
                pk,
                repr(bytes(data)),
                type(data),
                repr(bytes(instance.data)),
                type(instance.data),
            ),
        )
    else:
        testcase.assertEqual(
            data,
            instance.data,
            "Objects with PK=%s not equal; expected '%s' (%s), got '%s' (%s)"
            % (
                pk,
                data,
                type(data),
                instance,
                type(instance.data),
            ),
        )