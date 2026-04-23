async def async_setup_entry(hass: HomeAssistant, entry: TeslemetryConfigEntry) -> bool:
    """Set up Teslemetry config."""

    if "token" not in entry.data:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="token_data_malformed",
        )

    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="oauth_implementation_not_available",
        ) from err
    oauth_session = OAuth2Session(hass, entry, implementation)

    session = async_get_clientsession(hass)

    # Create API connection
    access_token = partial(_get_access_token, oauth_session)
    teslemetry = Teslemetry(
        session=session,
        access_token=access_token,
    )
    try:
        calls = await asyncio.gather(
            teslemetry.metadata(),
            teslemetry.products(),
        )
    except InvalidToken as e:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="auth_failed_invalid_token",
        ) from e
    except SubscriptionRequired as e:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="auth_failed_subscription_required",
        ) from e
    except TeslaFleetError as e:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="not_ready_api_error",
        ) from e

    scopes = calls[0]["scopes"]
    region = calls[0]["region"]
    vehicle_metadata = calls[0]["vehicles"]
    energy_site_metadata = calls[0]["energy_sites"]
    products = calls[1]["response"]

    device_registry = dr.async_get(hass)

    # Create array of classes
    vehicles: list[TeslemetryVehicleData] = []
    energysites: list[TeslemetryEnergyData] = []

    # Create the stream (created lazily when first vehicle is found)
    stream: TeslemetryStream | None = None

    # Remember each device identifier we create
    current_devices: set[tuple[str, str]] = set()

    # Track known devices for dynamic discovery (based on metadata access state)
    known_vins, known_site_ids = _get_subscribed_ids_from_metadata(calls[0])

    for product in products:
        if (
            "vin" in product
            and vehicle_metadata.get(product["vin"], {}).get("access")
            and Scope.VEHICLE_DEVICE_DATA in scopes
        ):
            vin = product["vin"]
            current_devices.add((DOMAIN, vin))

            # Create stream if required (for first vehicle)
            if not stream:
                stream = TeslemetryStream(
                    session,
                    access_token,
                    server=f"{region.lower()}.teslemetry.com",
                    parse_timestamp=True,
                    manual=True,
                )

            # Remove the protobuff 'cached_data' that we do not use to save memory
            product.pop("cached_data", None)
            vehicle = teslemetry.vehicles.create(vin)
            coordinator = TeslemetryVehicleDataCoordinator(
                hass, entry, vehicle, product
            )
            firmware = vehicle_metadata[vin].get("firmware")
            device = DeviceInfo(
                identifiers={(DOMAIN, vin)},
                manufacturer="Tesla",
                configuration_url="https://teslemetry.com/console",
                name=product["display_name"],
                model=vehicle.model,
                model_id=vin[3],
                serial_number=vin,
                sw_version=firmware,
            )

            poll = vehicle_metadata[vin].get("polling", False)

            entry.async_on_unload(
                stream.async_add_listener(
                    create_handle_vehicle_stream(vin, coordinator),
                    {"vin": vin},
                )
            )
            stream_vehicle = stream.get_vehicle(vin)

            vehicles.append(
                TeslemetryVehicleData(
                    api=vehicle,
                    config_entry=entry,
                    coordinator=coordinator,
                    poll=poll,
                    stream=stream,
                    stream_vehicle=stream_vehicle,
                    vin=vin,
                    firmware=firmware or "Unknown",
                    device=device,
                )
            )

        elif (
            "energy_site_id" in product
            and Scope.ENERGY_DEVICE_DATA in scopes
            and energy_site_metadata.get(str(product["energy_site_id"]), {}).get(
                "access"
            )
        ):
            site_id = product["energy_site_id"]

            powerwall = (
                product["components"]["battery"] or product["components"]["solar"]
            )
            wall_connector = "wall_connectors" in product["components"]
            if not powerwall and not wall_connector:
                LOGGER.debug(
                    "Skipping Energy Site %s as it has no components",
                    site_id,
                )
                continue

            current_devices.add((DOMAIN, str(site_id)))
            if wall_connector:
                current_devices |= {
                    (DOMAIN, c["din"]) for c in product["components"]["wall_connectors"]
                }

            energy_site = teslemetry.energySites.create(site_id)
            device = DeviceInfo(
                identifiers={(DOMAIN, str(site_id))},
                manufacturer="Tesla",
                configuration_url="https://teslemetry.com/console",
                name=product.get("site_name", "Energy Site"),
                serial_number=str(site_id),
            )

            # For initial setup, raise auth errors properly
            try:
                live_status = (await energy_site.live_status())["response"]
            except InvalidToken as e:
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="auth_failed_invalid_token",
                ) from e
            except SubscriptionRequired as e:
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="auth_failed_subscription_required",
                ) from e
            except Forbidden as e:
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="auth_failed_invalid_token",
                ) from e
            except TeslaFleetError as e:
                raise ConfigEntryNotReady(
                    translation_domain=DOMAIN,
                    translation_key="not_ready_api_error",
                ) from e

            energysites.append(
                TeslemetryEnergyData(
                    api=energy_site,
                    live_coordinator=(
                        TeslemetryEnergySiteLiveCoordinator(
                            hass, entry, energy_site, live_status
                        )
                        if isinstance(live_status, dict)
                        else None
                    ),
                    info_coordinator=TeslemetryEnergySiteInfoCoordinator(
                        hass, entry, energy_site, product
                    ),
                    history_coordinator=(
                        TeslemetryEnergyHistoryCoordinator(hass, entry, energy_site)
                        if powerwall
                        else None
                    ),
                    id=site_id,
                    device=device,
                )
            )

    # Run all first refreshes
    await asyncio.gather(
        *(async_setup_stream(hass, entry, vehicle) for vehicle in vehicles),
        *(
            vehicle.coordinator.async_config_entry_first_refresh()
            for vehicle in vehicles
            if vehicle.poll
        ),
        *(
            energysite.info_coordinator.async_config_entry_first_refresh()
            for energysite in energysites
        ),
    )

    # Register listeners for polling vehicle sw_version updates
    for vehicle_data in vehicles:
        if vehicle_data.poll:
            entry.async_on_unload(
                vehicle_data.coordinator.async_add_listener(
                    create_vehicle_polling_listener(
                        hass, vehicle_data.vin, vehicle_data.coordinator
                    )
                )
            )

    # Setup energy devices with models, versions, and listeners
    for energysite in energysites:
        async_setup_energy_device(hass, entry, energysite, device_registry)

    # Remove devices that are no longer present
    for device_entry in dr.async_entries_for_config_entry(
        device_registry, entry.entry_id
    ):
        if not any(
            identifier in current_devices for identifier in device_entry.identifiers
        ):
            LOGGER.debug("Removing stale device %s", device_entry.id)
            device_registry.async_update_device(
                device_id=device_entry.id,
                remove_config_entry_id=entry.entry_id,
            )

    metadata_coordinator = TeslemetryMetadataCoordinator(hass, entry, teslemetry)

    entry.runtime_data = TeslemetryData(
        vehicles=vehicles,
        energysites=energysites,
        scopes=scopes,
        stream=stream,
        metadata_coordinator=metadata_coordinator,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _setup_dynamic_discovery(
        hass,
        entry,
        metadata_coordinator,
        known_vins,
        known_site_ids,
    )

    if stream:
        entry.async_on_unload(stream.close)
        entry.async_create_background_task(hass, stream.listen(), "Teslemetry Stream")

    return True