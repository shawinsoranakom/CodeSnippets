def get_appxmanifest(ns):
    for k, v in APPXMANIFEST_NS.items():
        ET.register_namespace(k, v)
    ET.register_namespace("", APPXMANIFEST_NS["m"])

    xml = ET.parse(io.StringIO(APPXMANIFEST_TEMPLATE))
    NS = APPXMANIFEST_NS
    QN = ET.QName

    data = dict(APPX_DATA)
    for k, v in zip(APPX_PLATFORM_DATA["_keys"], APPX_PLATFORM_DATA[ns.arch]):
        data[k] = v

    node = xml.find("m:Identity", NS)
    for k in node.keys():
        value = data.get(k)
        if value:
            node.set(k, value)

    for node in xml.find("m:Properties", NS):
        value = data.get(node.tag.rpartition("}")[2])
        if value:
            node.text = value

    try:
        winver = tuple(int(i) for i in os.getenv("APPX_DATA_WINVER", "").split(".", maxsplit=3))
    except (TypeError, ValueError):
        winver = ()

    # Default "known good" version is 10.0.22000, first Windows 11 release
    winver = winver or (10, 0, 22000)

    if winver < (10, 0, 17763):
        winver = 10, 0, 17763
    find_or_add(xml, "m:Dependencies/m:TargetDeviceFamily").set(
        "MaxVersionTested", "{}.{}.{}.{}".format(*(winver + (0, 0, 0, 0)[:4]))
    )

    # Only for Python 3.11 and later. Older versions do not disable virtualization
    if (VER_MAJOR, VER_MINOR) >= (3, 11) and winver > (10, 0, 17763):
        disable_registry_virtualization(xml)

    app = add_application(
        ns,
        xml,
        "Python",
        "python{}".format(VER_DOT),
        ["python", "python{}".format(VER_MAJOR), "python{}".format(VER_DOT)],
        PYTHON_VE_DATA,
        "console",
        ("python.file", [".py"], '"%1" %*', "Python File", PY_PNG),
    )

    add_application(
        ns,
        xml,
        "PythonW",
        "pythonw{}".format(VER_DOT),
        ["pythonw", "pythonw{}".format(VER_MAJOR), "pythonw{}".format(VER_DOT)],
        PYTHONW_VE_DATA,
        "windows",
        ("python.windowedfile", [".pyw"], '"%1" %*', "Python File (no console)", PY_PNG),
    )

    if ns.include_pip and ns.include_launchers:
        add_application(
            ns,
            xml,
            "Pip",
            "pip{}".format(VER_DOT),
            ["pip", "pip{}".format(VER_MAJOR), "pip{}".format(VER_DOT)],
            PIP_VE_DATA,
            "console",
            ("python.wheel", [".whl"], 'install "%1"', "Python Wheel"),
        )

    if ns.include_idle and ns.include_launchers:
        add_application(
            ns,
            xml,
            "Idle",
            "idle{}".format(VER_DOT),
            ["idle", "idle{}".format(VER_MAJOR), "idle{}".format(VER_DOT)],
            IDLE_VE_DATA,
            "windows",
            None,
        )

    if (ns.source / SCCD_FILENAME).is_file():
        add_registry_entries(ns, xml)
        node = xml.find("m:Capabilities", NS)
        node = ET.SubElement(node, QN(NS["uap4"], "CustomCapability"))
        node.set("Name", "Microsoft.classicAppCompat_8wekyb3d8bbwe")

    buffer = io.BytesIO()
    xml.write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getbuffer()