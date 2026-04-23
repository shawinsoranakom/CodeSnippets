def __init__(self, attrs=None, validator_class=URLValidator):
        super().__init__(attrs={"class": "vURLField", **(attrs or {})})
        self.validator = validator_class()