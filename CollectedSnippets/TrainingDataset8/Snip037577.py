def __init__(self) -> None:
        super(PyplotGlobalUseWarning, self).__init__(
            msg=self._get_message(), config_option="deprecation.showPyplotGlobalUse"
        )