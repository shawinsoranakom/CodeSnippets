def __init__(self):
        if hasattr(settings, "ES"):
            self.ES_CONFIG = settings.ES
        else:
            self.ES_CONFIG = settings.get_base_config("es", {})

        for _ in range(ATTEMPT_TIME):
            try:
                if self._connect():
                    break
            except Exception as e:
                logging.warning(f"{str(e)}. Waiting Elasticsearch {self.ES_CONFIG['hosts']} to be healthy.")
                time.sleep(5)

        if not hasattr(self, "es_conn") or not self.es_conn or not self.es_conn.ping():
            msg = f"Elasticsearch {self.ES_CONFIG['hosts']} is unhealthy in 10s."
            logging.error(msg)
            raise Exception(msg)
        v = self.info.get("version", {"number": "8.11.3"})
        v = v["number"].split(".")[0]
        if int(v) < 8:
            msg = f"Elasticsearch version must be greater than or equal to 8, current version: {v}"
            logging.error(msg)
            raise Exception(msg)