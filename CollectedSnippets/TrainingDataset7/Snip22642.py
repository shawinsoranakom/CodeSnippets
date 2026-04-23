def __init__(self, **kwargs):
        fields = (
            CharField(),
            MultipleChoiceField(choices=beatles),
            SplitDateTimeField(),
        )
        super().__init__(fields, **kwargs)