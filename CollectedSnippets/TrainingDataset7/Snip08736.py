def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.missing_args_message == LabelCommand.missing_args_message:
            self.missing_args_message = self.missing_args_message % self.label