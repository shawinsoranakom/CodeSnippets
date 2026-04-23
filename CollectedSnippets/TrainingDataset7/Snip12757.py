def __new__(mcs, name, bases, attrs):
        new_class = super().__new__(mcs, name, bases, attrs)

        if "media" not in attrs:
            new_class.media = media_property(new_class)

        return new_class