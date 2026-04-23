def serialize(self):
        return serializer_factory(self.value.value).serialize()