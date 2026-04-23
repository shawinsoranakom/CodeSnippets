def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attr: dict[str, Any] = {}

        if self.watering_time is not None:
            attr[ATTR_WATERING_TIME] = self.watering_time

        if self.trigger_1 is not None:
            attr[ATTR_TRIGGER_1] = self.trigger_1

        if self.trigger_2 is not None:
            attr[ATTR_TRIGGER_2] = self.trigger_2

        if self.trigger_3 is not None:
            attr[ATTR_TRIGGER_3] = self.trigger_3

        if self.trigger_4 is not None:
            attr[ATTR_TRIGGER_4] = self.trigger_4

        if self.trigger_1_description is not None:
            attr[ATTR_TRIGGER_1_DESC] = self.trigger_1_description

        if self.trigger_2_description is not None:
            attr[ATTR_TRIGGER_2_DESC] = self.trigger_2_description

        if self.trigger_3_description is not None:
            attr[ATTR_TRIGGER_3_DESC] = self.trigger_3_description

        if self.trigger_4_description is not None:
            attr[ATTR_TRIGGER_4_DESC] = self.trigger_4_description

        return attr