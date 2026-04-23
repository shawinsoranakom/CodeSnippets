def _async_device_entities(
    data: ProtectData,
    klass: type[BaseProtectEntity],
    model_type: ModelType,
    descs: Sequence[ProtectEntityDescription],
    unadopted_descs: Sequence[ProtectEntityDescription] | None = None,
    ufp_device: ProtectAdoptableDeviceModel | None = None,
) -> list[BaseProtectEntity]:
    if not descs and not unadopted_descs:
        return []

    entities: list[BaseProtectEntity] = []
    devices = (
        [ufp_device]
        if ufp_device is not None
        else data.get_by_types({model_type}, ignore_unadopted=False)
    )
    auth_user = data.api.bootstrap.auth_user
    for device in devices:
        if TYPE_CHECKING:
            assert isinstance(device, ProtectAdoptableDeviceModel)
        if not device.is_adopted_by_us:
            if unadopted_descs:
                for description in unadopted_descs:
                    entities.append(
                        klass(
                            data,
                            device=device,
                            description=description,
                        )
                    )
                    _LOGGER.debug(
                        "Adding %s entity %s for %s",
                        klass.__name__,
                        description.key,
                        device.display_name,
                    )
            continue

        can_write = device.can_write(auth_user)
        for description in descs:
            if (perms := description.ufp_perm) is not None:
                if perms is PermRequired.WRITE and not can_write:
                    continue
                if perms is PermRequired.NO_WRITE and can_write:
                    continue
                if perms is PermRequired.DELETE and not device.can_delete(auth_user):
                    continue

            if not description.has_required(device):
                continue

            entities.append(
                klass(
                    data,
                    device=device,
                    description=description,
                )
            )
            _LOGGER.debug(
                "Adding %s entity %s for %s",
                klass.__name__,
                description.key,
                device.display_name,
            )

    return entities