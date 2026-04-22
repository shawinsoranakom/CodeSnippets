def _set_tornado_log_levels() -> None:
    if not config.get_option("global.developmentMode"):
        # Hide logs unless they're super important.
        # Example of stuff we don't care about: 404 about .js.map files.
        logging.getLogger("tornado.access").setLevel(logging.ERROR)
        logging.getLogger("tornado.application").setLevel(logging.ERROR)
        logging.getLogger("tornado.general").setLevel(logging.ERROR)