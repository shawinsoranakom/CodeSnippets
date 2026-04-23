async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the onboarding component."""
    store = OnboardingStorage(hass, STORAGE_VERSION, STORAGE_KEY, private=True)
    data: OnboardingStoreData | None
    if (data := await store.async_load()) is None:
        data = {"done": []}

    if TYPE_CHECKING:
        assert isinstance(data, dict)

    if STEP_USER not in data["done"]:
        # Users can already have created an owner account via the command line
        # If so, mark the user step as done.
        has_owner = False

        for user in await hass.auth.async_get_users():
            if user.is_owner:
                has_owner = True
                break

        if has_owner:
            data["done"].append(STEP_USER)
            await store.async_save(data)

    if set(data["done"]) == set(STEPS):
        return True

    hass.data[DOMAIN] = OnboardingData([], False, data)

    await views.async_setup(hass, data, store)

    return True