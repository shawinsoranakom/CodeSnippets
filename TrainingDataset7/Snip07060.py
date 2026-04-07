def err_handler(error_class, error_number, message):
    logger.error("GDAL_ERROR %d: %s", error_number, message)