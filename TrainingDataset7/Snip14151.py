def trigger_reload(filename):
    logger.info("%s changed, reloading.", filename)
    sys.exit(3)