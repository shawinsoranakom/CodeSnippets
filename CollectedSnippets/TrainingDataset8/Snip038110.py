def __init__(self, main_script_path: str, command_line: str):
        """Constructor.

        Parameters
        ----------
        main_script_path : str
            Path of the Python file from which this app is generated.

        command_line : string
            Command line as input by the user

        """
        basename = os.path.basename(main_script_path)

        self.main_script_path = os.path.abspath(main_script_path)
        self.script_folder = os.path.dirname(self.main_script_path)
        self.name = str(os.path.splitext(basename)[0])

        # The browser queue contains messages that haven't yet been
        # delivered to the browser. Periodically, the server flushes
        # this queue and delivers its contents to the browser.
        self._browser_queue = ForwardMsgQueue()

        self.command_line = command_line