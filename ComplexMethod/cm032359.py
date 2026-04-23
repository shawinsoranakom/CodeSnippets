def _invoke(self, **kwargs):
        if self.check_if_canceled("ExeSQL processing"):
            return

        def convert_decimals(obj):
            from decimal import Decimal
            import math
            if isinstance(obj, float):
                # Handle NaN and Infinity which are not valid JSON values
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return obj
            if isinstance(obj, Decimal):
                return float(obj)  # 或 str(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            return obj

        sql = kwargs.get("sql")
        if not sql:
            raise Exception("SQL for `ExeSQL` MUST not be empty.")

        if self.check_if_canceled("ExeSQL processing"):
            return

        vars = self.get_input_elements_from_text(sql)
        args = {}
        for k, o in vars.items():
            args[k] = o["value"]
            if not isinstance(args[k], str):
                try:
                    args[k] = json.dumps(args[k], ensure_ascii=False)
                except Exception:
                    args[k] = str(args[k])
            self.set_input_value(k, args[k])
        sql = self.string_format(sql, args)

        if self.check_if_canceled("ExeSQL processing"):
            return

        sqls = sql.split(";")
        if self._param.db_type in ["mysql", "mariadb"]:
            db = pymysql.connect(db=self._param.database, user=self._param.username, host=self._param.host,
                                 port=self._param.port, password=self._param.password)
        elif self._param.db_type == 'oceanbase':
            db = pymysql.connect(db=self._param.database, user=self._param.username, host=self._param.host,
                                 port=self._param.port, password=self._param.password, charset='utf8mb4')
        elif self._param.db_type == 'postgres':
            db = psycopg2.connect(dbname=self._param.database, user=self._param.username, host=self._param.host,
                                  port=self._param.port, password=self._param.password)
        elif self._param.db_type == 'mssql':
            conn_str = (
                    r'DRIVER={ODBC Driver 17 for SQL Server};'
                    r'SERVER=' + self._param.host + ',' + str(self._param.port) + ';'
                    r'DATABASE=' + self._param.database + ';'
                    r'UID=' + self._param.username + ';'
                    r'PWD=' + self._param.password
            )
            db = pyodbc.connect(conn_str)
        elif self._param.db_type == 'trino':
            try:
                import trino
                from trino.auth import BasicAuthentication
            except Exception:
                raise Exception("Missing dependency 'trino'. Please install: pip install trino")

            def _parse_catalog_schema(db: str):
                if not db:
                    return None, None
                if "." in db:
                    c, s = db.split(".", 1)
                elif "/" in db:
                    c, s = db.split("/", 1)
                else:
                    c, s = db, "default"
                return c, s

            catalog, schema = _parse_catalog_schema(self._param.database)
            if not catalog:
                raise Exception("For Trino, `database` must be 'catalog.schema' or at least 'catalog'.")

            http_scheme = "https" if os.environ.get("TRINO_USE_TLS", "0") == "1" else "http"
            auth = None
            if http_scheme == "https" and self._param.password:
                auth = BasicAuthentication(self._param.username, self._param.password)

            try:
                db = trino.dbapi.connect(
                    host=self._param.host,
                    port=int(self._param.port or 8080),
                    user=self._param.username or "ragflow",
                    catalog=catalog,
                    schema=schema or "default",
                    http_scheme=http_scheme,
                    auth=auth
                )
            except Exception as e:
                raise Exception("Database Connection Failed! \n" + str(e))
        elif self._param.db_type == 'IBM DB2':
            import ibm_db
            conn_str = (
                f"DATABASE={self._param.database};"
                f"HOSTNAME={self._param.host};"
                f"PORT={self._param.port};"
                f"PROTOCOL=TCPIP;"
                f"UID={self._param.username};"
                f"PWD={self._param.password};"
            )
            try:
                conn = ibm_db.connect(conn_str, "", "")
            except Exception as e:
                raise Exception("Database Connection Failed! \n" + str(e))

            try:
                sql_res = []
                formalized_content = []
                for single_sql in sqls:
                    if self.check_if_canceled("ExeSQL processing"):
                        return

                    single_sql = single_sql.replace("```", "").strip()
                    if not single_sql:
                        continue
                    single_sql = re.sub(r"\[ID:[0-9]+\]", "", single_sql)

                    stmt = ibm_db.exec_immediate(conn, single_sql)
                    rows = []
                    row = ibm_db.fetch_assoc(stmt)
                    while row and len(rows) < self._param.max_records:
                        if self.check_if_canceled("ExeSQL processing"):
                            return
                        rows.append(row)
                        row = ibm_db.fetch_assoc(stmt)

                    if not rows:
                        sql_res.append({"content": "No record in the database!"})
                        continue

                    df = pd.DataFrame(rows)
                    for col in df.columns:
                        if pd.api.types.is_datetime64_any_dtype(df[col]):
                            df[col] = df[col].dt.strftime("%Y-%m-%d")

                    df = df.where(pd.notnull(df), None)

                    sql_res.append(convert_decimals(df.to_dict(orient="records")))
                    formalized_content.append(df.to_markdown(index=False, floatfmt=".6f"))
            finally:
                with contextlib.suppress(Exception):
                    ibm_db.close(conn)

            self.set_output("json", sql_res)
            self.set_output("formalized_content", "\n\n".join(formalized_content))
            return self.output("formalized_content")
        try:
            cursor = db.cursor()
        except Exception as e:
            with contextlib.suppress(Exception):
                db.close()
            raise Exception("Database Connection Failed! \n" + str(e))

        try:
            sql_res = []
            formalized_content = []
            for single_sql in sqls:
                if self.check_if_canceled("ExeSQL processing"):
                    return

                single_sql = single_sql.replace('```', '').strip()
                if not single_sql:
                    continue
                single_sql = re.sub(r"\[ID:[0-9]+\]", "", single_sql)
                if re.match(r"^(insert|update|delete)\b", single_sql, flags=re.IGNORECASE):
                    sql_res.append({"content": "For security reasons, INSERT, UPDATE, and DELETE statements are not supported."})
                    formalized_content.append("For security reasons, INSERT, UPDATE, and DELETE statements are not supported.")
                    continue
                cursor.execute(single_sql)
                if cursor.rowcount == 0:
                    sql_res.append({"content": "No record in the database!"})
                    break
                if self._param.db_type == 'mssql':
                    single_res = pd.DataFrame.from_records(cursor.fetchmany(self._param.max_records),
                                                           columns=[desc[0] for desc in cursor.description])
                else:
                    single_res = pd.DataFrame([i for i in cursor.fetchmany(self._param.max_records)])
                    single_res.columns = [i[0] for i in cursor.description]

                for col in single_res.columns:
                    if pd.api.types.is_datetime64_any_dtype(single_res[col]):
                        single_res[col] = single_res[col].dt.strftime('%Y-%m-%d')

                single_res = single_res.where(pd.notnull(single_res), None)

                sql_res.append(convert_decimals(single_res.to_dict(orient='records')))
                formalized_content.append(single_res.to_markdown(index=False, floatfmt=".6f"))
        finally:
            with contextlib.suppress(Exception):
                cursor.close()
            with contextlib.suppress(Exception):
                db.close()

        self.set_output("json", sql_res)
        self.set_output("formalized_content", "\n\n".join(formalized_content))
        return self.output("formalized_content")