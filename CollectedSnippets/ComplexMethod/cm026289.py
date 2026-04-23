def _get_object_name(event: Event | dict[str, Any]) -> str:
    if isinstance(event, Event):
        event = event.unifi_dict()

    names = []
    types = set(event["smartDetectTypes"])
    metadata = event.get("metadata") or {}
    for thumb in metadata.get("detectedThumbnails", []):
        thumb_type = thumb.get("type")
        if thumb_type not in types:
            continue

        types.remove(thumb_type)
        if thumb_type == SmartDetectObjectType.VEHICLE.value:
            attributes = thumb.get("attributes") or {}
            color = attributes.get("color", {}).get("val", "")
            vehicle_type = attributes.get("vehicleType", {}).get("val", "vehicle")
            license_plate = metadata.get("licensePlate", {}).get("name")

            name = f"{color} {vehicle_type}".strip().title()
            if license_plate:
                types.remove(SmartDetectObjectType.LICENSE_PLATE.value)
                name = f"{name}: {license_plate}"
            names.append(name)
        else:
            smart_type = SmartDetectObjectType(thumb_type)
            names.append(smart_type.name.title().replace("_", " "))

    for raw in types:
        smart_type = SmartDetectObjectType(raw)
        names.append(smart_type.name.title().replace("_", " "))

    return ", ".join(sorted(names))