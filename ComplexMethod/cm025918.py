def get_device_serial(device: PyViCareDevice) -> str | None:
    """Get device serial for device if supported."""
    try:
        return device.getSerial()
    except PyViCareNotSupportedFeatureError:
        _LOGGER.debug("Device does not offer a 'device.serial' data point")
    except PyViCareRateLimitError as limit_exception:
        _LOGGER.debug("Vicare API rate limit exceeded: %s", limit_exception)
    except PyViCareInvalidDataError as invalid_data_exception:
        _LOGGER.debug("Invalid data from Vicare server: %s", invalid_data_exception)
    except PyViCareDeviceCommunicationError as comm_exception:
        _LOGGER.debug("Device communication error: %s", comm_exception)
    except PyViCareInternalServerError as server_exception:
        _LOGGER.debug("Vicare server error: %s", server_exception)
    except requests.exceptions.ConnectionError:
        _LOGGER.debug("Unable to retrieve data from ViCare server")
    except ValueError:
        _LOGGER.debug("Unable to decode data from ViCare server")
    return None