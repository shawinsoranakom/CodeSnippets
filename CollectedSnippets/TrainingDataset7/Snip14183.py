def request_processed(self, **kwargs):
        logger.debug("Request processed. Setting update_watches event.")
        self.processed_request.set()