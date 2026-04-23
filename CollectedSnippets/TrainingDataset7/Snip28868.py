def __init__(cls, name, bases, attrs):
                super().__init__(name, bases, attrs)
                cls.horns = 1 if "magic" in attrs else 0