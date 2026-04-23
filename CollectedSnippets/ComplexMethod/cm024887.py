async def test_cached_entity_property_class_attribute(hass: HomeAssistant) -> None:
    """Test entity properties on class level work in derived classes."""
    property_name = "attribution"
    values = ["abcd", "efgh"]

    class EntityWithClassAttribute1(entity.Entity):
        """A derived class which overrides an _attr_ from a parent."""

        _attr_attribution = values[0]

    class EntityWithClassAttribute2(entity.Entity, cached_properties={property}):
        """A derived class which overrides an _attr_ from a parent.

        This class also redundantly marks the overridden _attr_ as cached.
        """

        _attr_attribution = values[0]

    class EntityWithClassAttribute3(entity.Entity, cached_properties={property}):
        """A derived class which overrides an _attr_ from a parent.

        This class overrides the attribute property.
        """

        def __init__(self) -> None:
            self._attr_attribution = values[0]

        @cached_property
        def attribution(self) -> str | None:
            """Return the attribution."""
            return self._attr_attribution

    class EntityWithClassAttribute4(entity.Entity, cached_properties={property}):
        """A derived class which overrides an _attr_ from a parent.

        This class overrides the attribute property and the _attr_.
        """

        _attr_attribution = values[0]

        @cached_property
        def attribution(self) -> str | None:
            """Return the attribution."""
            return self._attr_attribution

    classes = (
        EntityWithClassAttribute1,
        EntityWithClassAttribute2,
        EntityWithClassAttribute3,
        EntityWithClassAttribute4,
    )

    entities: list[tuple[entity.Entity, entity.Entity]] = [
        (cls(), cls()) for cls in classes
    ]

    for ent in entities:
        assert getattr(ent[0], property_name) == values[0]
        assert getattr(ent[1], property_name) == values[0]

    # Test update
    for ent in entities:
        setattr(ent[0], f"_attr_{property_name}", values[1])
    for ent in entities:
        assert getattr(ent[0], property_name) == values[1]
        assert getattr(ent[1], property_name) == values[0]