def get_all_services():
        doc_engine = os.getenv("DOC_ENGINE", "elasticsearch")
        result = []
        configs = SERVICE_CONFIGS.configs
        for service_id, config in enumerate(configs):
            config_dict = config.to_dict()
            if config_dict["service_type"] == "retrieval":
                if config_dict["extra"]["retrieval_type"] != doc_engine:
                    continue
            try:
                service_detail = ServiceMgr.get_service_details(service_id)
                if "status" in service_detail:
                    config_dict["status"] = service_detail["status"]
                else:
                    config_dict["status"] = "timeout"
            except Exception as e:
                logging.warning(f"Can't get service details, error: {e}")
                config_dict["status"] = "timeout"
            if not config_dict["host"]:
                config_dict["host"] = "-"
            if not config_dict["port"]:
                config_dict["port"] = "-"
            result.append(config_dict)
        return result