def create_database_connection():
    """
    Try to create a database connection. Returns None if connection fails.
    """
    if not PSYCOPG2_AVAILABLE:
        logger.warning("psycopg2 not available - running in CSV-only mode")
        return None

    try:
        import psycopg2

        conn = psycopg2.connect("dbname=metrics")
        logger.info("Successfully connected to database")
        return conn
    except Exception as e:
        logger.warning(f"Failed to connect to database: {e}. Running in CSV-only mode")
        return None
