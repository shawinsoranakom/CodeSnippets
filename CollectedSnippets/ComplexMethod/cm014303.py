def get_intel_gpu_onboard(run_lambda):
    lst: list[str] = []
    platform = get_platform()
    if platform == "linux":
        txt = run_and_read_all(run_lambda, "xpu-smi discovery -j")
        if txt:
            try:
                obj = json.loads(txt)
                device_list = obj.get("device_list", [])
                if isinstance(device_list, list) and device_list:
                    lst.extend(f'* {device["device_name"]}' for device in device_list)
                else:
                    lst.append("N/A")
            except (ValueError, TypeError) as e:
                lst.append(txt)
                lst.append(str(e))
        else:
            lst.append("N/A")
    if platform in ["win32", "cygwin"]:
        txt = run_and_read_all(
            run_lambda,
            'powershell.exe "gwmi -Class Win32_PnpSignedDriver | where{$_.DeviceClass -eq \\"DISPLAY\\"\
            -and $_.Manufacturer -match \\"Intel\\"} | Select-Object -Property DeviceName | ConvertTo-Json"',
        )
        if txt:
            try:
                obj = json.loads(txt)
                if isinstance(obj, list) and obj:
                    lst.extend(f'* {device["DeviceName"]}' for device in obj)
                else:
                    lst.append(f'* {obj.get("DeviceName", "N/A")}')
            except ValueError as e:
                lst.append(txt)
                lst.append(str(e))
        else:
            lst.append("N/A")
    return "\n".join(lst)