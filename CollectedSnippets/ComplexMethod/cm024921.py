async def test_selector_serializer(
    hass: HomeAssistant, llm_context: llm.LLMContext
) -> None:
    """Test serialization of Selectors in Open API format."""
    api = await llm.async_get_api(hass, "assist", llm_context)
    selector_serializer = api.custom_serializer

    assert selector_serializer(selector.ActionSelector()) == {"type": "string"}
    assert selector_serializer(selector.AddonSelector()) == {"type": "string"}
    assert selector_serializer(selector.AreaSelector()) == {"type": "string"}
    assert selector_serializer(selector.AreaSelector({"multiple": True})) == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert selector_serializer(selector.AssistPipelineSelector()) == {"type": "string"}
    assert selector_serializer(
        selector.AttributeSelector({"entity_id": "sensor.test"})
    ) == {"type": "string"}
    assert selector_serializer(selector.BackupLocationSelector()) == {
        "type": "string",
        "pattern": "^(?:\\/backup|\\w+)$",
    }
    assert selector_serializer(selector.BooleanSelector()) == {"type": "boolean"}
    assert selector_serializer(selector.ColorRGBSelector()) == {
        "type": "array",
        "items": {"type": "number"},
        "maxItems": 3,
        "minItems": 3,
        "format": "RGB",
    }
    assert selector_serializer(selector.ColorTempSelector()) == {"type": "number"}
    assert selector_serializer(selector.ColorTempSelector({"min": 0, "max": 1000})) == {
        "type": "number",
        "minimum": 0,
        "maximum": 1000,
    }
    assert selector_serializer(
        selector.ColorTempSelector({"min_mireds": 100, "max_mireds": 1000})
    ) == {"type": "number", "minimum": 100, "maximum": 1000}
    assert selector_serializer(selector.ConditionSelector()) == {
        "type": "array",
        "items": {"nullable": True, "type": "string"},
    }
    assert selector_serializer(selector.ConfigEntrySelector()) == {"type": "string"}
    assert selector_serializer(selector.ConstantSelector({"value": "test"})) == {
        "type": "string",
        "enum": ["test"],
    }
    assert selector_serializer(selector.ConstantSelector({"value": 1})) == {
        "type": "integer",
        "enum": [1],
    }
    assert selector_serializer(selector.ConstantSelector({"value": True})) == {
        "type": "boolean",
        "enum": [True],
    }
    assert selector_serializer(selector.QrCodeSelector({"data": "test"})) == {
        "type": "string"
    }
    assert selector_serializer(selector.ConversationAgentSelector()) == {
        "type": "string"
    }
    assert selector_serializer(selector.CountrySelector()) == {
        "type": "string",
        "format": "ISO 3166-1 alpha-2",
    }
    assert selector_serializer(
        selector.CountrySelector({"countries": ["GB", "FR"]})
    ) == {"type": "string", "enum": ["GB", "FR"]}
    assert selector_serializer(selector.DateSelector()) == {
        "type": "string",
        "format": "date",
    }
    assert selector_serializer(selector.DateTimeSelector()) == {
        "type": "string",
        "format": "date-time",
    }
    assert selector_serializer(selector.DeviceSelector()) == {"type": "string"}
    assert selector_serializer(selector.DeviceSelector({"multiple": True})) == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert selector_serializer(selector.DurationSelector()) == {
        "type": "object",
        "properties": {
            "days": {"type": "number"},
            "hours": {"type": "number"},
            "minutes": {"type": "number"},
            "seconds": {"type": "number"},
            "milliseconds": {"type": "number"},
        },
        "required": [],
    }
    assert selector_serializer(selector.EntitySelector()) == {
        "type": "string",
        "format": "entity_id",
    }
    assert selector_serializer(selector.EntitySelector({"multiple": True})) == {
        "type": "array",
        "items": {"type": "string", "format": "entity_id"},
    }
    assert selector_serializer(selector.FloorSelector()) == {"type": "string"}
    assert selector_serializer(selector.FloorSelector({"multiple": True})) == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert selector_serializer(selector.IconSelector()) == {"type": "string"}
    assert selector_serializer(selector.LabelSelector()) == {"type": "string"}
    assert selector_serializer(selector.LabelSelector({"multiple": True})) == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert selector_serializer(selector.LanguageSelector()) == {
        "type": "string",
        "format": "RFC 5646",
    }
    assert selector_serializer(
        selector.LanguageSelector({"languages": ["en", "fr"]})
    ) == {"type": "string", "enum": ["en", "fr"]}
    assert selector_serializer(selector.LocationSelector()) == {
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"},
            "radius": {"type": "number"},
        },
        "required": ["latitude", "longitude"],
    }
    assert selector_serializer(selector.MediaSelector()) == {
        "type": "object",
        "properties": {
            "entity_id": {"type": "string"},
            "media_content_id": {"type": "string"},
            "media_content_type": {"type": "string"},
            "metadata": {"type": "object", "additionalProperties": True},
        },
        "required": ["media_content_id", "media_content_type"],
    }
    assert selector_serializer(selector.MediaSelector({"multiple": True})) == {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string"},
                "media_content_id": {"type": "string"},
                "media_content_type": {"type": "string"},
                "metadata": {"type": "object", "additionalProperties": True},
            },
            "required": ["media_content_id", "media_content_type"],
        },
    }
    assert selector_serializer(selector.NumberSelector({"mode": "box"})) == {
        "type": "number"
    }
    assert selector_serializer(selector.NumberSelector({"min": 30, "max": 100})) == {
        "type": "number",
        "minimum": 30,
        "maximum": 100,
    }
    assert selector_serializer(selector.ObjectSelector()) == {
        "type": "object",
        "additionalProperties": True,
    }
    assert selector_serializer(
        selector.ObjectSelector(
            {
                "fields": {
                    "name": {
                        "required": True,
                        "selector": {"text": {}},
                    },
                    "percentage": {
                        "selector": {"number": {"min": 30, "max": 100}},
                    },
                },
                "multiple": False,
                "label_field": "name",
            },
        )
    ) == {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "percentage": {"type": "number", "minimum": 30, "maximum": 100},
        },
        "required": ["name"],
    }
    assert selector_serializer(
        selector.ObjectSelector(
            {
                "fields": {
                    "name": {
                        "required": True,
                        "selector": {"text": {}},
                    },
                    "percentage": {
                        "selector": {"number": {"min": 30, "max": 100}},
                    },
                },
                "multiple": True,
                "label_field": "name",
            },
        )
    ) == {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "percentage": {
                    "type": "number",
                    "minimum": 30,
                    "maximum": 100,
                },
            },
            "required": ["name"],
        },
    }
    assert selector_serializer(
        selector.SelectSelector(
            {
                "options": [
                    {"value": "A", "label": "Letter A"},
                    {"value": "B", "label": "Letter B"},
                    {"value": "C", "label": "Letter C"},
                ]
            }
        )
    ) == {"type": "string", "enum": ["A", "B", "C"]}
    assert selector_serializer(
        selector.SelectSelector({"options": ["A", "B", "C"], "multiple": True})
    ) == {
        "type": "array",
        "items": {"type": "string", "enum": ["A", "B", "C"]},
        "uniqueItems": True,
    }
    assert selector_serializer(
        selector.StateSelector({"entity_id": "sensor.test"})
    ) == {"type": "string"}
    target_schema = selector_serializer(selector.TargetSelector())
    assert target_schema == {
        "type": "object",
        "properties": {
            "area_id": {"items": {"type": "string"}, "type": "array"},
            "device_id": {"items": {"type": "string"}, "type": "array"},
            "entity_id": {"items": {"type": "string"}, "type": "array"},
            "floor_id": {"items": {"type": "string"}, "type": "array"},
            "label_id": {"items": {"type": "string"}, "type": "array"},
        },
        "required": [],
    }

    assert selector_serializer(selector.TemplateSelector()) == {
        "type": "string",
        "format": "jinja2",
    }
    assert selector_serializer(selector.TextSelector()) == {"type": "string"}
    assert selector_serializer(selector.TextSelector({"multiple": True})) == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert selector_serializer(selector.ThemeSelector()) == {"type": "string"}
    assert selector_serializer(selector.TimeSelector()) == {
        "type": "string",
        "format": "time",
    }
    assert selector_serializer(selector.TriggerSelector()) == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert selector_serializer(selector.FileSelector({"accept": ".txt"})) == {
        "type": "string"
    }