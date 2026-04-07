def check_envelope(result, func, cargs, offset=-1):
    "Check a function that returns an OGR Envelope by reference."
    return ptr_byref(cargs, offset)