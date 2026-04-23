def match(self, service_info: BluetoothServiceInfoBleak) -> list[_T]:
        """Check for a match."""
        matches: list[_T] = []
        if (name := service_info.name) and (
            local_name_matchers := self.local_name.get(
                name[:LOCAL_NAME_MIN_MATCH_LENGTH]
            )
        ):
            matches.extend(
                matcher
                for matcher in local_name_matchers
                if ble_device_matches(matcher, service_info)
            )

        if (
            (service_data_uuid_set := self.service_data_uuid_set)
            and (service_data := service_info.service_data)
            and (matched_uuids := service_data_uuid_set.intersection(service_data))
        ):
            matches.extend(
                matcher
                for service_data_uuid in matched_uuids
                for matcher in self.service_data_uuid[service_data_uuid]
                if ble_device_matches(matcher, service_info)
            )

        if (
            (manufacturer_id_set := self.manufacturer_id_set)
            and (manufacturer_data := service_info.manufacturer_data)
            and (matched_ids := manufacturer_id_set.intersection(manufacturer_data))
        ):
            matches.extend(
                matcher
                for manufacturer_id in matched_ids
                for matcher in self.manufacturer_id[manufacturer_id]
                if ble_device_matches(matcher, service_info)
            )

        if (
            (service_uuid_set := self.service_uuid_set)
            and (service_uuids := service_info.service_uuids)
            and (matched_uuids := service_uuid_set.intersection(service_uuids))
        ):
            matches.extend(
                matcher
                for service_uuid in matched_uuids
                for matcher in self.service_uuid[service_uuid]
                if ble_device_matches(matcher, service_info)
            )

        return matches