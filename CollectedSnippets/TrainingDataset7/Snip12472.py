def __init__(self, *, max_value=None, min_value=None, step_size=None, **kwargs):
        self.max_value, self.min_value, self.step_size = max_value, min_value, step_size
        if kwargs.get("localize") and self.widget == NumberInput:
            # Localized number input is not well supported on most browsers
            kwargs.setdefault("widget", super().widget)
        super().__init__(**kwargs)

        if max_value is not None:
            self.validators.append(validators.MaxValueValidator(max_value))
        if min_value is not None:
            self.validators.append(validators.MinValueValidator(min_value))
        if step_size is not None:
            self.validators.append(
                validators.StepValueValidator(step_size, offset=min_value)
            )