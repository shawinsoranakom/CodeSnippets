async def test_db_connect():
    req = await get_request_json()
    try:
        if req["db_type"] in ["mysql", "mariadb"]:
            db = MySQLDatabase(req["database"], user=req["username"], host=req["host"], port=req["port"],
                               password=req["password"])
        elif req["db_type"] == "oceanbase":
            db = MySQLDatabase(req["database"], user=req["username"], host=req["host"], port=req["port"],
                               password=req["password"], charset="utf8mb4")
        elif req["db_type"] == 'postgres':
            db = PostgresqlDatabase(req["database"], user=req["username"], host=req["host"], port=req["port"],
                                    password=req["password"])
        elif req["db_type"] == 'mssql':
            import pyodbc
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={req['host']},{req['port']};"
                f"DATABASE={req['database']};"
                f"UID={req['username']};"
                f"PWD={req['password']};"
            )
            db = pyodbc.connect(connection_string)
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        elif req["db_type"] == 'IBM DB2':
            import ibm_db
            conn_str = (
                f"DATABASE={req['database']};"
                f"HOSTNAME={req['host']};"
                f"PORT={req['port']};"
                f"PROTOCOL=TCPIP;"
                f"UID={req['username']};"
                f"PWD={req['password']};"
            )
            redacted_conn_str = (
                f"DATABASE={req['database']};"
                f"HOSTNAME={req['host']};"
                f"PORT={req['port']};"
                f"PROTOCOL=TCPIP;"
                f"UID={req['username']};"
                f"PWD=****;"
            )
            logging.info(redacted_conn_str)
            conn = ibm_db.connect(conn_str, "", "")
            stmt = ibm_db.exec_immediate(conn, "SELECT 1 FROM sysibm.sysdummy1")
            ibm_db.fetch_assoc(stmt)
            ibm_db.close(conn)
            return get_json_result(data="Database Connection Successful!")
        elif req["db_type"] == 'trino':
            def _parse_catalog_schema(db_name: str):
                if not db_name:
                    return None, None
                if "." in db_name:
                    catalog_name, schema_name = db_name.split(".", 1)
                elif "/" in db_name:
                    catalog_name, schema_name = db_name.split("/", 1)
                else:
                    catalog_name, schema_name = db_name, "default"
                return catalog_name, schema_name
            try:
                import trino
                import os
            except Exception as e:
                return server_error_response(f"Missing dependency 'trino'. Please install: pip install trino, detail: {e}")

            catalog, schema = _parse_catalog_schema(req["database"])
            if not catalog:
                return server_error_response("For Trino, 'database' must be 'catalog.schema' or at least 'catalog'.")

            http_scheme = "https" if os.environ.get("TRINO_USE_TLS", "0") == "1" else "http"

            auth = None
            if http_scheme == "https" and req.get("password"):
                auth = trino.BasicAuthentication(req.get("username") or "ragflow", req["password"])

            conn = trino.dbapi.connect(
                host=req["host"],
                port=int(req["port"] or 8080),
                user=req["username"] or "ragflow",
                catalog=catalog,
                schema=schema or "default",
                http_scheme=http_scheme,
                auth=auth
            )
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchall()
            cur.close()
            conn.close()
            return get_json_result(data="Database Connection Successful!")
        else:
            return server_error_response("Unsupported database type.")
        if req["db_type"] != 'mssql':
            db.connect()
        db.close()

        return get_json_result(data="Database Connection Successful!")
    except Exception as e:
        return server_error_response(e)