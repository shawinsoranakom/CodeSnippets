def serializerTestTextFieldPK(self, format):
    data = [
        (
            pk_obj,
            1,
            TextPKData,
            """This is a long piece of text.
            It contains line breaks.
            Several of them.
            The end.""",
        ),
    ]
    assert_serializer(self, format, data)