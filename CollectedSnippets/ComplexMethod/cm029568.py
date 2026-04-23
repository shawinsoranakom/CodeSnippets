def get_appx_layout(ns):
    if not ns.include_appxmanifest:
        return

    yield "AppxManifest.xml", ("AppxManifest.xml", get_appxmanifest(ns))
    yield "_resources.xml", ("_resources.xml", get_resources_xml(ns))
    icons = ns.source / "PC" / "icons"
    for px in [44, 50, 150]:
        src = icons / "pythonx{}.png".format(px)
        yield f"_resources/pythonx{px}.png", src
        yield f"_resources/pythonx{px}$targetsize-{px}_altform-unplated.png", src
    for px in [44, 150]:
        src = icons / "pythonwx{}.png".format(px)
        yield f"_resources/pythonwx{px}.png", src
        yield f"_resources/pythonwx{px}$targetsize-{px}_altform-unplated.png", src
    if ns.include_idle and ns.include_launchers:
        for px in [44, 150]:
            src = icons / "idlex{}.png".format(px)
            yield f"_resources/idlex{px}.png", src
            yield f"_resources/idlex{px}$targetsize-{px}_altform-unplated.png", src
    yield f"_resources/py.png", icons / "py.png"
    sccd = ns.source / SCCD_FILENAME
    if sccd.is_file():
        # This should only be set for side-loading purposes.
        sccd = _fixup_sccd(ns, sccd, os.getenv("APPX_DATA_SHA256"))
        yield sccd.name, sccd