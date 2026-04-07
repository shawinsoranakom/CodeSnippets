def enqueue(self, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"{self.prefix}Task enqueued.")