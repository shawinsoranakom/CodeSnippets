def buildDMG():
    """
    Create DMG containing the rootDir.
    """
    outdir = os.path.join(WORKDIR, 'diskimage')
    if os.path.exists(outdir):
        shutil.rmtree(outdir)

    # We used to use the deployment target as the last characters of the
    # installer file name. With the introduction of weaklinked installer
    # variants, we may have two variants with the same file name, i.e.
    # both ending in '10.9'.  To avoid this, we now use the major/minor
    # version numbers of the macOS version we are building on.
    # Also, as of macOS 11, operating system version numbering has
    # changed from three components to two, i.e.
    #   10.14.1, 10.14.2, ...
    #   10.15.1, 10.15.2, ...
    #   11.1, 11.2, ...
    #   12.1, 12.2, ...
    # (A further twist is that, when running on macOS 11, binaries built
    # on older systems may be shown an operating system version of 10.16
    # instead of 11.  We should not run into that situation here.)
    # Also we should use "macos" instead of "macosx" going forward.
    #
    # To maintain compatibility for legacy variants, the file name for
    # builds on macOS 10.15 and earlier remains:
    #   python-3.x.y-macosx10.z.{dmg->pkg}
    #   e.g. python-3.9.4-macosx10.9.{dmg->pkg}
    # and for builds on macOS 11+:
    #   python-3.x.y-macosz.{dmg->pkg}
    #   e.g. python-3.9.4-macos11.{dmg->pkg}

    build_tuple = getBuildTuple()
    if build_tuple[0] < 11:
        os_name = 'macosx'
        build_system_version = '%s.%s' % build_tuple
    else:
        os_name = 'macos'
        build_system_version = str(build_tuple[0])
    imagepath = os.path.join(outdir,
                    'python-%s-%s%s'%(getFullVersion(),os_name,build_system_version))
    if INCLUDE_TIMESTAMP:
        imagepath = imagepath + '-%04d-%02d-%02d'%(time.localtime()[:3])
    imagepath = imagepath + '.dmg'

    os.mkdir(outdir)

    # Try to mitigate race condition in certain versions of macOS, e.g. 10.9,
    # when hdiutil create fails with  "Resource busy".  For now, just retry
    # the create a few times and hope that it eventually works.

    volname='Python %s'%(getFullVersion())
    cmd = ("hdiutil create -format UDRW -volname %s -srcfolder %s -size 100m %s"%(
            shellQuote(volname),
            shellQuote(os.path.join(WORKDIR, 'installer')),
            shellQuote(imagepath + ".tmp.dmg" )))
    for i in range(5):
        fd = os.popen(cmd, 'r')
        data = fd.read()
        xit = fd.close()
        if not xit:
            break
        sys.stdout.write(data)
        print(" -- retrying hdiutil create")
        time.sleep(5)
    else:
        raise RuntimeError("command failed: %s"%(cmd,))

    if not os.path.exists(os.path.join(WORKDIR, "mnt")):
        os.mkdir(os.path.join(WORKDIR, "mnt"))
    runCommand("hdiutil attach %s -mountroot %s"%(
        shellQuote(imagepath + ".tmp.dmg"), shellQuote(os.path.join(WORKDIR, "mnt"))))

    # Custom icon for the DMG, shown when the DMG is mounted.
    shutil.copy("../Icons/Disk Image.icns",
            os.path.join(WORKDIR, "mnt", volname, ".VolumeIcon.icns"))
    runCommand("SetFile -a C %s/"%(
            shellQuote(os.path.join(WORKDIR, "mnt", volname)),))

    runCommand("hdiutil detach %s"%(shellQuote(os.path.join(WORKDIR, "mnt", volname))))

    setIcon(imagepath + ".tmp.dmg", "../Icons/Disk Image.icns")
    runCommand("hdiutil convert %s -format UDZO -o %s"%(
            shellQuote(imagepath + ".tmp.dmg"), shellQuote(imagepath)))
    setIcon(imagepath, "../Icons/Disk Image.icns")

    os.unlink(imagepath + ".tmp.dmg")

    return imagepath