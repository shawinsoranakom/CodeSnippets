async def async_call(
        self, hass: HomeAssistant, tool_input: ToolInput, llm_context: LLMContext
    ) -> JsonObjectType:
        """Call the action."""

        for field, validator in self.parameters.schema.items():
            if field not in tool_input.tool_args:
                continue
            if isinstance(validator, selector.AreaSelector):
                area_reg = ar.async_get(hass)
                if validator.config.get("multiple"):
                    areas: list[ar.AreaEntry] = []
                    for area in tool_input.tool_args[field]:
                        areas.extend(intent.find_areas(area, area_reg))
                    tool_input.tool_args[field] = list({area.id for area in areas})
                else:
                    area = tool_input.tool_args[field]
                    area = list(intent.find_areas(area, area_reg))[0].id
                    tool_input.tool_args[field] = area

            elif isinstance(validator, selector.FloorSelector):
                floor_reg = fr.async_get(hass)
                if validator.config.get("multiple"):
                    floors: list[fr.FloorEntry] = []
                    for floor in tool_input.tool_args[field]:
                        floors.extend(intent.find_floors(floor, floor_reg))
                    tool_input.tool_args[field] = list(
                        {floor.floor_id for floor in floors}
                    )
                else:
                    floor = tool_input.tool_args[field]
                    floor = list(intent.find_floors(floor, floor_reg))[0].floor_id
                    tool_input.tool_args[field] = floor

        result = await hass.services.async_call(
            self._domain,
            self._action,
            tool_input.tool_args,
            context=llm_context.context,
            blocking=True,
            return_response=True,
        )

        return {"success": True, "result": result}