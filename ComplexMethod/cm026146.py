async def _handle_pick_region(
        self,
        step_id: str,
        next_step: str | None,
        user_input: dict[str, str] | None,
        last_step: bool = False,
    ) -> ConfigFlowResult:
        """Handle picking a (sub)region."""
        if self.selected_region:
            source = self.selected_region["regionChildIds"]
        else:
            source = self.states

        if user_input is not None:
            # Only offer to browse subchildren if picked region wasn't the previously picked one
            if (
                not self.selected_region
                or user_input[CONF_REGION] != self.selected_region["regionId"]
            ):
                self.selected_region = _find(source, user_input[CONF_REGION])

                if (
                    next_step
                    and self.selected_region
                    and self.selected_region["regionChildIds"]
                ):
                    return await getattr(self, f"async_step_{next_step}")()

            return await self._async_finish_flow()

        regions = {}
        if self.selected_region and step_id != "district":
            regions[self.selected_region["regionId"]] = self.selected_region[
                "regionName"
            ]

        regions.update(_make_regions_object(source))

        schema = vol.Schema(
            {
                vol.Required(CONF_REGION): vol.In(regions),
            }
        )

        return self.async_show_form(
            step_id=step_id, data_schema=schema, last_step=last_step
        )