def test_custom_encoders():
    class safe_datetime(datetime):
        pass

    class MyDict(TypedDict):
        dt_field: safe_datetime

    instance = MyDict(dt_field=safe_datetime.now())

    encoded_instance = jsonable_encoder(
        instance, custom_encoder={safe_datetime: lambda o: o.strftime("%H:%M:%S")}
    )
    assert encoded_instance["dt_field"] == instance["dt_field"].strftime("%H:%M:%S")

    encoded_instance = jsonable_encoder(
        instance, custom_encoder={datetime: lambda o: o.strftime("%H:%M:%S")}
    )
    assert encoded_instance["dt_field"] == instance["dt_field"].strftime("%H:%M:%S")

    encoded_instance2 = jsonable_encoder(instance)
    assert encoded_instance2["dt_field"] == instance["dt_field"].isoformat()