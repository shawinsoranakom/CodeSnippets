def __init__(self, attrs=None, format=None):
        attrs = {"class": "vTimeField", "size": "8", **(attrs or {})}
        super().__init__(attrs=attrs, format=format)