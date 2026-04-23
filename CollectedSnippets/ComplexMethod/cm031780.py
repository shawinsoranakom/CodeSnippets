def do_unixy_check(manifest, args):
    """Check headers & library using "Unixy" tools (GCC/clang, binutils)"""
    okay = True

    # Get all macros first: we'll need feature macros like HAVE_FORK and
    # MS_WINDOWS for everything else
    present_macros = gcc_get_limited_api_macros(['Include/Python.h'])
    feature_macros = {m.name for m in manifest.select({'feature_macro'})}
    feature_macros &= present_macros

    # Check that we have all needed macros
    expected_macros = {item.name for item in manifest.select({'macro'})}
    missing_macros = expected_macros - present_macros
    okay &= _report_unexpected_items(
        missing_macros,
        'Some macros from are not defined from "Include/Python.h" '
        'with Py_LIMITED_API:')

    expected_symbols = {item.name for item in manifest.select(
        {'function', 'data'}, include_abi_only=True, ifdef=feature_macros,
    )}

    # Check the static library (*.a)
    LIBRARY = sysconfig.get_config_var("LIBRARY")
    if not LIBRARY:
        raise Exception("failed to get LIBRARY variable from sysconfig")
    if os.path.exists(LIBRARY):
        okay &= binutils_check_library(
            manifest, LIBRARY, expected_symbols, dynamic=False)

    # Check the dynamic library (*.so)
    LDLIBRARY = sysconfig.get_config_var("LDLIBRARY")
    if not LDLIBRARY:
        raise Exception("failed to get LDLIBRARY variable from sysconfig")
    okay &= binutils_check_library(
            manifest, LDLIBRARY, expected_symbols, dynamic=False)

    # Check definitions in the header files
    expected_defs = {item.name for item in manifest.select(
        {'function', 'data'}, include_abi_only=False, ifdef=feature_macros,
    )}
    found_defs = gcc_get_limited_api_definitions(['Include/Python.h'])
    missing_defs = expected_defs - found_defs
    okay &= _report_unexpected_items(
        missing_defs,
        'Some expected declarations were not declared in '
        '"Include/Python.h" with Py_LIMITED_API:')

    # Some Limited API macros are defined in terms of private symbols.
    # These are not part of Limited API (even though they're defined with
    # Py_LIMITED_API). They must be part of the Stable ABI, though.
    private_symbols = {n for n in expected_symbols if n.startswith('_')}
    extra_defs = found_defs - expected_defs - private_symbols
    okay &= _report_unexpected_items(
        extra_defs,
        'Some extra declarations were found in "Include/Python.h" '
        'with Py_LIMITED_API:')

    return okay