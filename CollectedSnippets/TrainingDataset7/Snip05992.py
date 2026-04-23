def __init__(self, attrs=None):
        super().__init__(attrs={"class": self.class_name, **(attrs or {})})