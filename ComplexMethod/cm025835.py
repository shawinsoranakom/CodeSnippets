def __init__(
        self,
        camera_entity: str,
        name: str | None,
        doods: PyDOODS,
        detector: dict[str, Any],
        config: dict[str, Any],
    ) -> None:
        """Initialize the DOODS entity."""
        self._attr_camera_entity = camera_entity
        if name:
            self._attr_name = name
        else:
            self._attr_name = f"Doods {split_entity_id(camera_entity)[1]}"
        self._doods = doods
        self._file_out: list[template.Template] = config[CONF_FILE_OUT]
        self._detector_name = detector["name"]

        # detector config and aspect ratio
        self._width = None
        self._height = None
        self._aspect = None
        if detector["width"] and detector["height"]:
            self._width = detector["width"]
            self._height = detector["height"]
            self._aspect = self._width / self._height

        # the base confidence
        dconfig: dict[str, float] = {}
        confidence: float = config[CONF_CONFIDENCE]

        # handle labels and specific detection areas
        labels: list[str | dict[str, Any]] = config[CONF_LABELS]
        self._label_areas = {}
        self._label_covers = {}
        for label in labels:
            if isinstance(label, dict):
                label_name: str = label[CONF_NAME]
                if label_name not in detector["labels"] and label_name != "*":
                    _LOGGER.warning("Detector does not support label %s", label_name)
                    continue

                # If label confidence is not specified, use global confidence
                if not (label_confidence := label.get(CONF_CONFIDENCE)):
                    label_confidence = confidence
                if label_name not in dconfig or dconfig[label_name] > label_confidence:
                    dconfig[label_name] = label_confidence

                # Label area
                label_area = label.get(CONF_AREA)
                self._label_areas[label_name] = [0, 0, 1, 1]
                self._label_covers[label_name] = True
                if label_area:
                    self._label_areas[label_name] = [
                        label_area[CONF_TOP],
                        label_area[CONF_LEFT],
                        label_area[CONF_BOTTOM],
                        label_area[CONF_RIGHT],
                    ]
                    self._label_covers[label_name] = label_area[CONF_COVERS]
            else:
                if label not in detector["labels"] and label != "*":
                    _LOGGER.warning("Detector does not support label %s", label)
                    continue
                self._label_areas[label] = [0, 0, 1, 1]
                self._label_covers[label] = True
                if label not in dconfig or dconfig[label] > confidence:
                    dconfig[label] = confidence

        if not dconfig:
            dconfig["*"] = confidence

        # Handle global detection area
        self._area = [0, 0, 1, 1]
        self._covers = True
        if area_config := config.get(CONF_AREA):
            self._area = [
                area_config[CONF_TOP],
                area_config[CONF_LEFT],
                area_config[CONF_BOTTOM],
                area_config[CONF_RIGHT],
            ]
            self._covers = area_config[CONF_COVERS]

        self._dconfig = dconfig
        self._matches: dict[str, list[dict[str, Any]]] = {}
        self._total_matches = 0
        self._last_image = None
        self._process_time = 0.0