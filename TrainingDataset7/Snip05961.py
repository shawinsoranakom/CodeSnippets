def __init__(self, attrs=None, format=None):
        attrs = {"class": "vDateField", "size": "10", **(attrs or {})}
        super().__init__(attrs=attrs, format=format)