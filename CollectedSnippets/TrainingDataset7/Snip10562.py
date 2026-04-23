def serialize(cls, value):
        return serializer_factory(value).serialize()