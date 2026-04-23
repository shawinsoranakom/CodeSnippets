def serialize(self, value):
        return serializer_factory(value).serialize()[0]