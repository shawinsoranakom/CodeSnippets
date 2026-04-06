def module_error_output(filename, module_name):
    return """Traceback (most recent call last):
  File "{0}", line 1, in <module>
    import {1}
ModuleNotFoundError: No module named '{1}'""".format(
        filename, module_name
    )