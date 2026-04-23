def setUp(self):
        super().setUp()
        logging_conf = """
[loggers]
keys=root
[handlers]
keys=stream
[formatters]
keys=simple
[logger_root]
handlers=stream
[handler_stream]
class=StreamHandler
formatter=simple
args=(sys.stdout,)
[formatter_simple]
format=%(message)s
"""
        temp_file = NamedTemporaryFile()
        temp_file.write(logging_conf.encode())
        temp_file.flush()
        self.addCleanup(temp_file.close)
        self.write_settings(
            "settings.py",
            sdict={
                "LOGGING_CONFIG": '"logging.config.fileConfig"',
                "LOGGING": 'r"%s"' % temp_file.name,
            },
        )