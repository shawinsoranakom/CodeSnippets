def __init__(self):
        if hasattr(settings, "INFINITY"):
            self.INFINITY_CONFIG = settings.INFINITY
        else:
            self.INFINITY_CONFIG = settings.get_base_config("infinity", {
                "uri": "infinity:23817",
                "postgres_port": 5432,
                "db_name": "default_db"
            })

        raw_pool_max_size = os.environ.get("INFINITY_POOL_MAX_SIZE", "4")
        try:
            self.pool_max_size = int(raw_pool_max_size)
        except ValueError as e:
            raise ValueError("INFINITY_POOL_MAX_SIZE must be a positive integer") from e
        if self.pool_max_size < 1:
            raise ValueError("INFINITY_POOL_MAX_SIZE must be >= 1")

        infinity_uri = self.INFINITY_CONFIG["uri"]
        if ":" in infinity_uri:
            host, port = infinity_uri.split(":")
            self.infinity_uri = infinity.common.NetworkAddress(host, int(port))

        self.conn_pool = None
        for _ in range(24):
            conn_pool = None
            inf_conn = None
            try:
                conn_pool = ConnectionPool(self.infinity_uri, max_size=self.pool_max_size)
                inf_conn = conn_pool.get_conn()
                res = inf_conn.show_current_node()
                if res.error_code == ErrorCode.OK and res.server_status in ["started", "alive"]:
                    self.conn_pool = conn_pool
                    break
                logging.warning(f"Infinity status: {res.server_status}. Waiting Infinity {infinity_uri} to be healthy.")
                time.sleep(5)
            except Exception as e:
                logging.warning(f"{str(e)}. Waiting Infinity {infinity_uri} to be healthy.")
                time.sleep(5)
            finally:
                if inf_conn is not None and conn_pool is not None:
                    conn_pool.release_conn(inf_conn)
                if conn_pool is not None and conn_pool is not self.conn_pool:
                    conn_pool.destroy()

        if self.conn_pool is None:
            msg = f"Infinity {infinity_uri} is unhealthy in 120s."
            logging.error(msg)
            raise Exception(msg)

        logging.info(f"Infinity {infinity_uri} is healthy. Connection pool max_size={self.pool_max_size}")