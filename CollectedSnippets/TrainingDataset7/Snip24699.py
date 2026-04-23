def _get_postgis_func(self, func):
            if func == "postgis_lib_version":
                if self.version is None:
                    raise ProgrammingError
                else:
                    return self.version
            elif func == "version":
                pass
            else:
                raise NotImplementedError("This function was not expected to be called")