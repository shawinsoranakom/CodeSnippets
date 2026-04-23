async def test_home_assistant_error_subclass(hass: HomeAssistant) -> None:
    """Test __str__ method on an HomeAssistantError subclass."""

    class _SubExceptionDefault(HomeAssistantError):
        """Sub class, default with generated message."""

    class _SubExceptionConstructor(HomeAssistantError):
        """Sub class with constructor, no generated message."""

        def __init__(
            self,
            custom_arg: str,
            translation_domain: str | None = None,
            translation_key: str | None = None,
            translation_placeholders: dict[str, str] | None = None,
        ) -> None:
            super().__init__(
                translation_domain=translation_domain,
                translation_key=translation_key,
                translation_placeholders=translation_placeholders,
            )
            self.custom_arg = custom_arg

    class _SubExceptionConstructorGenerate(HomeAssistantError):
        """Sub class with constructor, with generated message."""

        generate_message: bool = True

        def __init__(
            self,
            custom_arg: str,
            translation_domain: str | None = None,
            translation_key: str | None = None,
            translation_placeholders: dict[str, str] | None = None,
        ) -> None:
            super().__init__(
                translation_domain=translation_domain,
                translation_key=translation_key,
                translation_placeholders=translation_placeholders,
            )
            self.custom_arg = custom_arg

    class _SubExceptionGenerate(HomeAssistantError):
        """Sub class, no generated message."""

        generate_message: bool = True

    class _SubClassWithExceptionGroup(HomeAssistantError, BaseExceptionGroup):
        """Sub class with exception group, no generated message."""

    class _SubClassWithExceptionGroupGenerate(HomeAssistantError, BaseExceptionGroup):
        """Sub class with exception group and generated message."""

        generate_message: bool = True

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={"component.test.exceptions.bla.message": "{bla} from cache"},
    ):
        # A subclass without a constructor generates a message by default
        with pytest.raises(HomeAssistantError) as exc:
            raise _SubExceptionDefault(
                translation_domain="test",
                translation_key="bla",
                translation_placeholders={"bla": "Bla"},
            )
        assert str(exc.value) == "Bla from cache"

        # A subclass with a constructor that does not parse `args` to the super class
        with pytest.raises(HomeAssistantError) as exc:
            raise _SubExceptionConstructor(
                "custom arg",
                translation_domain="test",
                translation_key="bla",
                translation_placeholders={"bla": "Bla"},
            )
        assert str(exc.value) == "Bla from cache"
        with pytest.raises(HomeAssistantError) as exc:
            raise _SubExceptionConstructor(
                "custom arg",
            )
        assert str(exc.value) == ""

        # A subclass with a constructor that generates the message
        with pytest.raises(HomeAssistantError) as exc:
            raise _SubExceptionConstructorGenerate(
                "custom arg",
                translation_domain="test",
                translation_key="bla",
                translation_placeholders={"bla": "Bla"},
            )
        assert str(exc.value) == "Bla from cache"

        # A subclass without overridden constructors and passed args
        # defaults to the passed args
        with pytest.raises(HomeAssistantError) as exc:
            raise _SubExceptionDefault(
                ValueError("wrong value"),
                translation_domain="test",
                translation_key="bla",
                translation_placeholders={"bla": "Bla"},
            )
        assert str(exc.value) == "wrong value"

        # A subclass without overridden constructors and passed args
        # and generate_message = True,  generates a message
        with pytest.raises(HomeAssistantError) as exc:
            raise _SubExceptionGenerate(
                ValueError("wrong value"),
                translation_domain="test",
                translation_key="bla",
                translation_placeholders={"bla": "Bla"},
            )
        assert str(exc.value) == "Bla from cache"

        # A subclass with an ExceptionGroup subclass requires a message to be passed.
        # As we pass args, we will not generate the message.
        # The __str__ constructor defaults to that of the super class.
        with pytest.raises(HomeAssistantError) as exc:
            raise _SubClassWithExceptionGroup(
                "group message",
                [ValueError("wrong value"), TypeError("wrong type")],
                translation_domain="test",
                translation_key="bla",
                translation_placeholders={"bla": "Bla"},
            )
        assert str(exc.value) == "group message (2 sub-exceptions)"
        with pytest.raises(HomeAssistantError) as exc:
            raise _SubClassWithExceptionGroup(
                "group message",
                [ValueError("wrong value"), TypeError("wrong type")],
            )
        assert str(exc.value) == "group message (2 sub-exceptions)"

        # A subclass with an ExceptionGroup subclass requires a message to be passed.
        # The `generate_message` flag is set.`
        # The __str__ constructor will return the generated message.
        with pytest.raises(HomeAssistantError) as exc:
            raise _SubClassWithExceptionGroupGenerate(
                "group message",
                [ValueError("wrong value"), TypeError("wrong type")],
                translation_domain="test",
                translation_key="bla",
                translation_placeholders={"bla": "Bla"},
            )
        assert str(exc.value) == "Bla from cache"