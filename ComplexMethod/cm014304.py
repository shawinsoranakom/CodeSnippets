def get_cpu_info(run_lambda):
    rc, out, err = 0, "", ""
    if get_platform() == "linux":
        rc, out, err = run_lambda("lscpu")
    elif get_platform() == "win32":
        rc, out, err = run_lambda(
            'powershell.exe "gwmi -Class Win32_Processor | Select-Object -Property Name,Manufacturer,Family,\
            Architecture,ProcessorType,DeviceID,CurrentClockSpeed,MaxClockSpeed,L2CacheSize,L2CacheSpeed,Revision\
            | ConvertTo-Json"'
        )
        if rc == 0:
            lst = []
            try:
                obj = json.loads(out)
                if type(obj) is list:
                    for o in obj:
                        lst.append("----------------------")
                        lst.extend([f"{k}: {v}" for (k, v) in o.items()])
                else:
                    lst.extend([f"{k}: {v}" for (k, v) in obj.items()])
            except ValueError as e:
                lst.append(out)
                lst.append(str(e))
            out = "\n".join(lst)
    elif get_platform() == "darwin":
        rc, out, err = run_lambda("sysctl -n machdep.cpu.brand_string")
    cpu_info = "None"
    if rc == 0:
        cpu_info = out
    else:
        cpu_info = err
    return cpu_info