def serializerTestNullValueStingField(self, format):
    data = [
        (data_obj, 1, BinaryData, None),
        (data_obj, 2, CharData, None),
        (data_obj, 3, EmailData, None),
        (data_obj, 4, FilePathData, None),
        (data_obj, 5, SlugData, None),
        (data_obj, 6, TextData, None),
    ]
    assert_serializer(self, format, data)