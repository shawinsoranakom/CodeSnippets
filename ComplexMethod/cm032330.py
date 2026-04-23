def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the provider with Aliyun credentials.

        Args:
            config: Configuration dictionary with keys:
                - access_key_id: Aliyun AccessKey ID
                - access_key_secret: Aliyun AccessKey Secret
                - account_id: Aliyun primary account ID
                - region: Region (default: "cn-hangzhou")
                - template_name: Optional sandbox template name
                - timeout: Request timeout in seconds (default: 30, max 30)

        Returns:
            True if initialization successful, False otherwise
        """
        # Get values from config or environment variables
        access_key_id = config.get("access_key_id") or os.getenv("AGENTRUN_ACCESS_KEY_ID")
        access_key_secret = config.get("access_key_secret") or os.getenv("AGENTRUN_ACCESS_KEY_SECRET")
        account_id = config.get("account_id") or os.getenv("AGENTRUN_ACCOUNT_ID")
        region = config.get("region") or os.getenv("AGENTRUN_REGION", "cn-hangzhou")

        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.account_id = account_id
        self.region = region
        self.template_name = config.get("template_name", "")
        self.timeout = min(config.get("timeout", 30), 30)  # Max 30 seconds

        logger.info(f"Aliyun Code Interpreter: Initializing with account_id={self.account_id}, region={self.region}")

        # Validate required fields
        if not self.access_key_id or not self.access_key_secret:
            logger.error("Aliyun Code Interpreter: Missing access_key_id or access_key_secret")
            return False

        if not self.account_id:
            logger.error("Aliyun Code Interpreter: Missing account_id (primary account ID)")
            return False

        # Create SDK configuration
        try:
            logger.info(f"Aliyun Code Interpreter: Creating Config object with account_id={self.account_id}")
            self._config = Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                account_id=self.account_id,
                region_id=self.region,
                timeout=self.timeout,
            )
            logger.info("Aliyun Code Interpreter: Config object created successfully")

            # Verify connection with health check
            if not self.health_check():
                logger.error(f"Aliyun Code Interpreter: Health check failed for region {self.region}")
                return False

            self._initialized = True
            logger.info(f"Aliyun Code Interpreter: Initialized successfully for region {self.region}")
            return True

        except Exception as e:
            logger.error(f"Aliyun Code Interpreter: Initialization failed - {str(e)}")
            return False