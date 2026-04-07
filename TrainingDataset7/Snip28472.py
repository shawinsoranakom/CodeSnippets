def __new__(cls, name, bases, attrs):
        new = super().__new__(cls, name, bases, attrs)
        new.base_fields = {}
        return new