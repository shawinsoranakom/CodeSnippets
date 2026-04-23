def _cleanup_json(self, json):
        for extra_device in self.extra_devices:
            json["devices"][extra_device["id"]] = extra_device

        if self.test_devices is not None:
            new_devices = {}
            for json_device in json["devices"].items():
                if json_device[1]["label"] in self.test_devices:
                    new_devices.update([json_device])
            json["devices"] = new_devices

        if self.test_groups is not None:
            new_groups = {}
            for json_group in json["groups"].items():
                if json_group[1]["label"] in self.test_groups:
                    new_groups.update([json_group])
            json["groups"] = new_groups

        return json