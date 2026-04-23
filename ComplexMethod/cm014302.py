def get_intel_gpu_driver_version(run_lambda):
    lst = []
    platform = get_platform()
    if platform == "linux":
        pkgs = {  # type: ignore[var-annotated]
            "dpkg": {
                "intel-opencl-icd",
                "libze1",
                "level-zero",
            },
            "dnf": {
                "intel-opencl",
                "level-zero",
            },
            "yum": {
                "intel-opencl",
                "level-zero",
            },
            "zypper": {
                "intel-opencl",
                "level-zero",
            },
        }.get(_detect_linux_pkg_manager(), {})
        for pkg in pkgs:
            ver = get_linux_pkg_version(run_lambda, pkg)
            if ver != "N/A":
                lst.append(f"* {pkg}:\t{ver}")
    if platform in ["win32", "cygwin"]:
        txt = run_and_read_all(
            run_lambda,
            'powershell.exe "gwmi -Class Win32_PnpSignedDriver | where{$_.DeviceClass -eq \\"DISPLAY\\"\
            -and $_.Manufacturer -match \\"Intel\\"} | Select-Object -Property DeviceName,DriverVersion,DriverDate\
            | ConvertTo-Json"',
        )
        try:
            obj = json.loads(txt)
            if type(obj) is list:
                for o in obj:
                    lst.append(
                        f'* {o["DeviceName"]}: {o["DriverVersion"]} ({o["DriverDate"]})'
                    )
            else:
                lst.append(f'* {obj["DriverVersion"]} ({obj["DriverDate"]})')
        except ValueError as e:
            lst.append(txt)
            lst.append(str(e))
    return "\n".join(lst)