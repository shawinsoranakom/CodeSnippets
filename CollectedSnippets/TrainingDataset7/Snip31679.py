def serializerTestPK0(self, format):
    # FK to an object with PK of 0. This won't work on MySQL without the
    # NO_AUTO_VALUE_ON_ZERO SQL mode since it won't let you create an object
    # with an autoincrement primary key of 0.
    data = [
        (data_obj, 0, Anchor, "Anchor 0"),
        (fk_obj, 1, FKData, 0),
    ]
    assert_serializer(self, format, data)