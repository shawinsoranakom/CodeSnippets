def std_call(func):
    """
    Return the correct STDCALL function for certain OSR routines on Win32
    platforms.
    """
    if os.name == "nt":
        return lwingdal[func]
    else:
        return lgdal[func]