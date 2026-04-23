def _get_device_names(self) -> list[str]:
        """Obtain the list of names of connected GPUs as identified in :attr:`_handles`.

        Returns
        -------
        The list of connected AMD GPU names
        """
        retval = []
        for device in self._handles:
            if self._is_wsl:
                retval.append(torch.cuda.get_device_name(device))
            else:
                name = self._from_sysfs_file(os.path.join(device, "product_name"))
                number = self._from_sysfs_file(os.path.join(device, "product_number"))
                if name or number:  # product_name or product_number populated
                    self._log("debug", f"Got name from product_name: '{name}', product_number: "
                                       f"'{number}'")
                    retval.append(f"{name + ' ' if name else ''}{number}")
                    continue

                device_id = self._from_sysfs_file(os.path.join(device, "device"))
                self._log("debug", f"Got device_id: '{device_id}'")

                if not device_id:  # Can't get device name
                    retval.append("Not found")
                    continue
                try:
                    lookup = int(device_id, 0)
                except ValueError:
                    retval.append(device_id)
                    continue

                device_name = _DEVICE_LOOKUP.get(lookup, device_id)
                retval.append(device_name)

        self._log("debug", f"Device names: {retval}")
        return retval