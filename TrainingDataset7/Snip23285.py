def __init__(self, required=True, widget=None, label=None, initial=None):
        fields = (
            CharField(),
            MultipleChoiceField(choices=WidgetTest.beatles),
            SplitDateTimeField(),
        )
        super().__init__(
            fields, required=required, widget=widget, label=label, initial=initial
        )