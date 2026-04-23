def __init__(self, context, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context.dicts.append(self)
        self.context = context