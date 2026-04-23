def fill_empty_fields(self):
        """Override any defaults with values from legacy enviroment variables"""
        if self.host is None:
            self.host = os.getenv('DB_HOST')
        if self.port is None:
            self.port = int(os.getenv('DB_PORT', '5432'))
        if self.name is None:
            self.name = os.getenv('DB_NAME', 'openhands')
        if self.user is None:
            self.user = os.getenv('DB_USER', 'postgres')
        if self.password is None:
            self.password = SecretStr(os.getenv('DB_PASS', 'postgres').strip())
        if self.gcp_db_instance is None:
            self.gcp_db_instance = os.getenv('GCP_DB_INSTANCE')
        if self.gcp_project is None:
            self.gcp_project = os.getenv('GCP_PROJECT')
        if self.gcp_region is None:
            self.gcp_region = os.getenv('GCP_REGION')
        return self