def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["category"].queryset = Category.objects.filter(
                    slug__contains="test"
                )