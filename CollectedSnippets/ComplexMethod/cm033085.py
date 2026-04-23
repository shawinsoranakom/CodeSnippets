def __init__(self, secret_id: str = None, secret_key: str = None, region: str = "ap-guangzhou",
                 table_result_type: str = None, markdown_image_response_type: str = None):
        super().__init__()

        # First initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # Log received parameters
        self.logger.info(f"[TCADP] Initializing with parameters - table_result_type: {table_result_type}, markdown_image_response_type: {markdown_image_response_type}")

        # Priority: read configuration from RAGFlow configuration system (service_conf.yaml)
        try:
            tcadp_parser = get_base_config("tcadp_config", {})
            if isinstance(tcadp_parser, dict) and tcadp_parser:
                self.secret_id = secret_id or tcadp_parser.get("secret_id")
                self.secret_key = secret_key or tcadp_parser.get("secret_key")
                self.region = region or tcadp_parser.get("region", "ap-guangzhou")
                # Set table_result_type and markdown_image_response_type from config or parameters
                self.table_result_type = table_result_type if table_result_type is not None else tcadp_parser.get("table_result_type", "1")
                self.markdown_image_response_type = markdown_image_response_type if markdown_image_response_type is not None else tcadp_parser.get("markdown_image_response_type", "1")

            else:
                self.logger.error("[TCADP] Please configure tcadp_config in service_conf.yaml first")
                # If config file is empty, use provided parameters or defaults
                self.secret_id = secret_id
                self.secret_key = secret_key
                self.region = region or "ap-guangzhou"
                self.table_result_type = table_result_type if table_result_type is not None else "1"
                self.markdown_image_response_type = markdown_image_response_type if markdown_image_response_type is not None else "1"

        except ImportError:
            self.logger.info("[TCADP] Configuration module import failed")
            # If config file is not available, use provided parameters or defaults
            self.secret_id = secret_id
            self.secret_key = secret_key
            self.region = region or "ap-guangzhou"
            self.table_result_type = table_result_type if table_result_type is not None else "1"
            self.markdown_image_response_type = markdown_image_response_type if markdown_image_response_type is not None else "1"

        # Log final values
        self.logger.info(f"[TCADP] Final values - table_result_type: {self.table_result_type}, markdown_image_response_type: {self.markdown_image_response_type}")

        if not self.secret_id or not self.secret_key:
            raise ValueError("[TCADP] Please set Tencent Cloud API keys, configure tcadp_config in service_conf.yaml")