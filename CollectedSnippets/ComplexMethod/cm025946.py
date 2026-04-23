def serialize(self) -> dict[str, Any]:
        """Serialize the selector to a dictionary."""

        options: dict[str, Any] = {
            "write": {"required": self.write_required} if self.write else False,
            "state": {"required": self.state_required} if self.state else False,
            "passive": self.passive,
        }
        if self.dpt is not None:
            if isinstance(self.dpt, list):
                options["dptClasses"] = self.dpt
            else:
                options["dptSelect"] = [
                    {
                        "value": item.value,
                        "translation_key": item.value.replace(".", "_"),
                        "dpt": dpt_string_to_dict(item.value),  # used for filtering GAs
                    }
                    for item in self.dpt
                ]
        if self.valid_dpt is not None:
            options["validDPTs"] = [dpt_string_to_dict(dpt) for dpt in self.valid_dpt]

        return {
            "type": self.selector_type,
            "options": options,
        }