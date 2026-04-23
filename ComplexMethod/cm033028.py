def __init__(
        self,
        db_type: str,
        host: str,
        port: int,
        database: str,
        query: str,
        content_columns: str,
        metadata_columns: Optional[str] = None,
        id_column: Optional[str] = None,
        timestamp_column: Optional[str] = None,
        batch_size: int = INDEX_BATCH_SIZE,
    ) -> None:
        """
        Initialize the RDBMS connector.

        Args:
            db_type: Database type ('mysql' or 'postgresql')
            host: Database host
            port: Database port
            database: Database name
            query: SQL query to execute (e.g., "SELECT * FROM products WHERE status = 'active'")
            content_columns: Comma-separated column names to use for document content
            metadata_columns: Comma-separated column names to use as metadata (optional)
            id_column: Column to use as unique document ID (optional, will generate hash if not provided)
            timestamp_column: Column to use for incremental sync (optional, must be datetime/timestamp type)
            batch_size: Number of documents per batch
        """
        self.db_type = DatabaseType(db_type.lower())
        self.host = host.strip()
        self.port = port
        self.database = database.strip()
        self.query = query.strip()
        self.content_columns = [c.strip() for c in content_columns.split(",") if c.strip()]
        self.metadata_columns = [c.strip() for c in (metadata_columns or "").split(",") if c.strip()]
        self.id_column = id_column.strip() if id_column else None
        self.timestamp_column = timestamp_column.strip() if timestamp_column else None
        self.batch_size = batch_size

        self._connection = None
        self._credentials: Dict[str, Any] = {}