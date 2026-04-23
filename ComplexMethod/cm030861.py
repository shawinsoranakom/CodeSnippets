def setUpModule():
    if support.verbose:
        plats = {
            'Mac': platform.mac_ver,
            'Windows': platform.win32_ver,
        }
        for name, func in plats.items():
            plat = func()
            if plat and plat[0]:
                plat = '%s %r' % (name, plat)
                break
        else:
            plat = repr(platform.platform())
        print("test_ssl: testing with %r %r" %
            (ssl.OPENSSL_VERSION, ssl.OPENSSL_VERSION_INFO))
        print("          under %s" % plat)
        print("          HAS_SNI = %r" % ssl.HAS_SNI)
        print("          OP_ALL = 0x%8x" % ssl.OP_ALL)
        try:
            print("          OP_NO_TLSv1_1 = 0x%8x" % ssl.OP_NO_TLSv1_1)
        except AttributeError:
            pass

    for filename in [
        CERTFILE, BYTES_CERTFILE,
        ONLYCERT, ONLYKEY, BYTES_ONLYCERT, BYTES_ONLYKEY,
        SIGNED_CERTFILE, SIGNED_CERTFILE2, SIGNING_CA,
        BADCERT, BADKEY, EMPTYCERT]:
        if not os.path.exists(filename):
            raise support.TestFailed("Can't read certificate file %r" % filename)

    thread_info = threading_helper.threading_setup()
    unittest.addModuleCleanup(threading_helper.threading_cleanup, *thread_info)