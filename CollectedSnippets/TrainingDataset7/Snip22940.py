def __init__(self, *args, **kwargs):
                fields = [CharField(), CharField(required=False)]
                super().__init__(fields, *args, **kwargs)