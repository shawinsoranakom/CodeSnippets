def side_effect(datatype, *args, **kwargs):
        if datatype in fail_types:
            raise AsusRouterError(f"{datatype} unavailable")
        # Return valid mock data for other types
        if datatype == AsusData.CLIENTS:
            return {}
        if datatype == AsusData.NETWORK:
            return {}
        if datatype == AsusData.SYSINFO:
            return {}
        if datatype == AsusData.TEMPERATURE:
            return {}
        if datatype == AsusData.CPU:
            return {}
        if datatype == AsusData.RAM:
            return {}
        if datatype == AsusData.BOOTTIME:
            return {}
        return {}