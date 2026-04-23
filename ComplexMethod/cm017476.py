def load_geos():
    # Custom library path set?
    try:
        from django.conf import settings

        lib_path = settings.GEOS_LIBRARY_PATH
    except (AttributeError, ImportError, ImproperlyConfigured, OSError):
        lib_path = None

    # Setting the appropriate names for the GEOS-C library.
    if lib_path:
        lib_names = None
    elif os.name == "nt":
        # Windows NT libraries
        lib_names = ["geos_c", "libgeos_c-1"]
    elif os.name == "posix":
        # *NIX libraries
        lib_names = ["geos_c", "GEOS"]
    else:
        raise ImportError('Unsupported OS "%s"' % os.name)

    # Using the ctypes `find_library` utility to find the path to the GEOS
    # shared library. This is better than manually specifying each library name
    # and extension (e.g., libgeos_c.[so|so.1|dylib].).
    if lib_names:
        for lib_name in lib_names:
            lib_path = find_library(lib_name)
            if lib_path is not None:
                break

    # No GEOS library could be found.
    if lib_path is None:
        raise ImportError(
            'Could not find the GEOS library (tried "%s"). '
            "Try setting GEOS_LIBRARY_PATH in your settings." % '", "'.join(lib_names)
        )
    # Getting the GEOS C library. The C interface (CDLL) is used for
    # both *NIX and Windows.
    # See the GEOS C API source code for more details on the library function
    # calls: https://libgeos.org/doxygen/geos__c_8h_source.html
    _lgeos = CDLL(lib_path)
    # Here we set up the prototypes for the GEOS_init_r and GEOS_finish_r
    # routines, as well as the context handler setters.
    # These functions aren't actually called until they are
    # attached to a GEOS context handle -- this actually occurs in
    # geos/prototypes/threadsafe.py.
    _lgeos.GEOS_init_r.restype = CONTEXT_PTR
    _lgeos.GEOS_finish_r.argtypes = [CONTEXT_PTR]
    _lgeos.GEOSContext_setErrorHandler_r.argtypes = [CONTEXT_PTR, ERRORFUNC]
    _lgeos.GEOSContext_setNoticeHandler_r.argtypes = [CONTEXT_PTR, NOTICEFUNC]
    # Set restype for compatibility across 32 and 64-bit platforms.
    _lgeos.GEOSversion.restype = c_char_p
    return _lgeos