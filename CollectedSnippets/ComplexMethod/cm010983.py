def __init__(self, remote_device: str | torch.device):
        PARSE_ERROR = (
            f"Could not parse remote_device: {remote_device}. The valid format is "
            "'<workername>/<device>' or 'rank:<rank>/<device>' or '<device>'"
        )
        self._worker_name = None
        self._rank = None
        self._device: str | int | torch.device | None = None

        if isinstance(remote_device, torch.device):
            self._device = remote_device
        elif isinstance(remote_device, str):
            fields = remote_device.split("/")
            if len(fields) == 2:
                self._worker_name, self._device = fields
            elif len(fields) == 1:
                # Check if this is a valid device.
                if _remote_device._is_valid_local_device(fields[0]):
                    self._device = fields[0]
                else:
                    self._worker_name = fields[0]
                    self._device = "cpu"
            else:
                raise ValueError(PARSE_ERROR)
        else:
            raise TypeError(f"Invalid type for remote_device: {type(remote_device)}")

        # Do some basic sanity check (no empty string)
        if self._worker_name is not None and not self._worker_name:
            raise ValueError(PARSE_ERROR)

        # Validate the device.
        self._device = torch.device(self._device)

        # Check for rank based format.
        if self._worker_name is not None:
            fields = self._worker_name.split(":")
            if len(fields) == 2:
                # rank:<rank>/device format, extract rank
                if fields[0] == "rank" and fields[1].isdigit():
                    self._rank = int(fields[1])  # type: ignore[assignment]
                    self._worker_name = None
                else:
                    raise ValueError(PARSE_ERROR)
            elif len(fields) > 2:
                raise ValueError(PARSE_ERROR)