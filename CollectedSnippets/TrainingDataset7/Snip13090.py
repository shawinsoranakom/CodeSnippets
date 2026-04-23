def __post_init__(self):
        self.get_backend().validate_task(self)