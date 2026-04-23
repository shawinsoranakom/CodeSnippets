def __init__(self):
        self.info = {}
        logger.info(f"Use OpenSearch {settings.OS['hosts']} as the doc engine.")
        for _ in range(ATTEMPT_TIME):
            try:
                self.os = OpenSearch(
                    settings.OS["hosts"].split(","),
                    http_auth=(settings.OS["username"], settings.OS[
                        "password"]) if "username" in settings.OS and "password" in settings.OS else None,
                    verify_certs=False,
                    timeout=600
                )
                if self.os:
                    self.info = self.os.info()
                    break
            except Exception as e:
                logger.warning(f"{str(e)}. Waiting OpenSearch {settings.OS['hosts']} to be healthy.")
                time.sleep(5)
        if not self.os.ping():
            msg = f"OpenSearch {settings.OS['hosts']} is unhealthy in 120s."
            logger.error(msg)
            raise Exception(msg)
        v = self.info.get("version", {"number": "2.18.0"})
        v = v["number"].split(".")[0]
        if int(v) < 2:
            msg = f"OpenSearch version must be greater than or equal to 2, current version: {v}"
            logger.error(msg)
            raise Exception(msg)
        fp_mapping = os.path.join(get_project_base_directory(), "conf", "os_mapping.json")
        if not os.path.exists(fp_mapping):
            msg = f"OpenSearch mapping file not found at {fp_mapping}"
            logger.error(msg)
            raise Exception(msg)
        with open(fp_mapping, "r") as f:
            self.mapping = json.load(f)
        logger.info(f"OpenSearch {settings.OS['hosts']} is healthy.")