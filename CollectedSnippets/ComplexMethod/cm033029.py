def _get_connection(self):
        """Create and return a database connection."""
        if self._connection is not None:
            return self._connection

        username = self._credentials.get("username")
        password = self._credentials.get("password")

        if self.db_type == DatabaseType.MYSQL:
            try:
                import mysql.connector
            except ImportError:
                raise ConnectorValidationError(
                    "MySQL connector not installed. Please install mysql-connector-python."
                )
            try:
                self._connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=username,
                    password=password,
                    charset='utf8mb4',
                    use_unicode=True,
                )
            except Exception as e:
                raise ConnectorValidationError(f"Failed to connect to MySQL: {e}")
        elif self.db_type == DatabaseType.POSTGRESQL:
            try:
                import psycopg2
            except ImportError:
                raise ConnectorValidationError(
                    "PostgreSQL connector not installed. Please install psycopg2-binary."
                )
            try:
                self._connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    dbname=self.database,
                    user=username,
                    password=password,
                )
            except Exception as e:
                raise ConnectorValidationError(f"Failed to connect to PostgreSQL: {e}")

        return self._connection