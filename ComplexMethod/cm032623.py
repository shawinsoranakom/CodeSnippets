def test_test_db_connect_dialect_matrix_unit(monkeypatch):
    module = _load_canvas_module(monkeypatch)

    class _FakeDB:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.connected = 0
            self.closed = 0

        def connect(self):
            self.connected += 1

        def close(self):
            self.closed += 1

    mysql_objs = []
    postgres_objs = []

    def _mysql_ctor(*args, **kwargs):
        obj = _FakeDB(*args, **kwargs)
        mysql_objs.append(obj)
        return obj

    def _postgres_ctor(*args, **kwargs):
        obj = _FakeDB(*args, **kwargs)
        postgres_objs.append(obj)
        return obj

    monkeypatch.setattr(module, "MySQLDatabase", _mysql_ctor)
    monkeypatch.setattr(module, "PostgresqlDatabase", _postgres_ctor)

    def _run_case(payload):
        _set_request_json(monkeypatch, module, payload)
        return _run(inspect.unwrap(module.test_db_connect)())

    req_base = {
        "database": "db",
        "username": "user",
        "host": "host",
        "port": 3306,
        "password": "pwd",
    }

    res = _run_case({**req_base, "db_type": "mysql"})
    assert res["code"] == module.RetCode.SUCCESS
    assert mysql_objs[-1].connected == 1
    assert mysql_objs[-1].closed == 1

    res = _run_case({**req_base, "db_type": "mariadb"})
    assert res["code"] == module.RetCode.SUCCESS
    assert mysql_objs[-1].connected == 1

    res = _run_case({**req_base, "db_type": "oceanbase"})
    assert res["code"] == module.RetCode.SUCCESS
    assert mysql_objs[-1].kwargs["charset"] == "utf8mb4"

    res = _run_case({**req_base, "db_type": "postgres"})
    assert res["code"] == module.RetCode.SUCCESS
    assert postgres_objs[-1].closed == 1

    mssql_calls = {}

    class _MssqlCursor:
        def execute(self, sql):
            mssql_calls["sql"] = sql

        def close(self):
            mssql_calls["cursor_closed"] = True

    class _MssqlConn:
        def cursor(self):
            mssql_calls["cursor_opened"] = True
            return _MssqlCursor()

        def close(self):
            mssql_calls["conn_closed"] = True

    pyodbc_mod = ModuleType("pyodbc")

    def _pyodbc_connect(conn_str):
        mssql_calls["conn_str"] = conn_str
        return _MssqlConn()

    pyodbc_mod.connect = _pyodbc_connect
    monkeypatch.setitem(sys.modules, "pyodbc", pyodbc_mod)
    res = _run_case({**req_base, "db_type": "mssql"})
    assert res["code"] == module.RetCode.SUCCESS
    assert "DRIVER={ODBC Driver 17 for SQL Server}" in mssql_calls["conn_str"]
    assert mssql_calls["sql"] == "SELECT 1"

    ibm_calls = {}
    ibm_db_mod = ModuleType("ibm_db")

    def _ibm_connect(conn_str, *_args):
        ibm_calls["conn_str"] = conn_str
        return "ibm-conn"

    def _ibm_exec_immediate(conn, sql):
        ibm_calls["exec"] = (conn, sql)
        return "ibm-stmt"

    ibm_db_mod.connect = _ibm_connect
    ibm_db_mod.exec_immediate = _ibm_exec_immediate
    ibm_db_mod.fetch_assoc = lambda stmt: ibm_calls.update({"fetch": stmt}) or {"one": 1}
    ibm_db_mod.close = lambda conn: ibm_calls.update({"close": conn})
    monkeypatch.setitem(sys.modules, "ibm_db", ibm_db_mod)
    res = _run_case({**req_base, "db_type": "IBM DB2"})
    assert res["code"] == module.RetCode.SUCCESS
    assert ibm_calls["exec"] == ("ibm-conn", "SELECT 1 FROM sysibm.sysdummy1")

    monkeypatch.setitem(sys.modules, "trino", None)
    res = _run_case({**req_base, "db_type": "trino", "database": "catalog.schema"})
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "Missing dependency 'trino'" in res["message"]

    trino_calls = {"connect": [], "auth": []}

    class _TrinoCursor:
        def execute(self, sql):
            trino_calls["sql"] = sql

        def fetchall(self):
            trino_calls["fetched"] = True
            return [(1,)]

        def close(self):
            trino_calls["cursor_closed"] = True

    class _TrinoConn:
        def cursor(self):
            return _TrinoCursor()

        def close(self):
            trino_calls["conn_closed"] = True

    trino_mod = ModuleType("trino")
    trino_mod.BasicAuthentication = lambda user, password: trino_calls["auth"].append((user, password)) or ("auth", user)
    trino_mod.dbapi = SimpleNamespace(connect=lambda **kwargs: trino_calls["connect"].append(kwargs) or _TrinoConn())
    monkeypatch.setitem(sys.modules, "trino", trino_mod)

    res = _run_case({**req_base, "db_type": "trino", "database": ""})
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "catalog.schema" in res["message"]

    monkeypatch.setenv("TRINO_USE_TLS", "1")
    res = _run_case({**req_base, "db_type": "trino", "database": "cat.schema"})
    assert res["code"] == module.RetCode.SUCCESS
    assert trino_calls["connect"][-1]["catalog"] == "cat"
    assert trino_calls["connect"][-1]["schema"] == "schema"
    assert trino_calls["auth"][-1] == ("user", "pwd")

    res = _run_case({**req_base, "db_type": "trino", "database": "cat/schema"})
    assert res["code"] == module.RetCode.SUCCESS
    assert trino_calls["connect"][-1]["catalog"] == "cat"
    assert trino_calls["connect"][-1]["schema"] == "schema"

    res = _run_case({**req_base, "db_type": "trino", "database": "catalog"})
    assert res["code"] == module.RetCode.SUCCESS
    assert trino_calls["connect"][-1]["catalog"] == "catalog"
    assert trino_calls["connect"][-1]["schema"] == "default"

    res = _run_case({**req_base, "db_type": "unknown"})
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "Unsupported database type." in res["message"]

    class _BoomDB(_FakeDB):
        def connect(self):
            raise RuntimeError("connect boom")

    monkeypatch.setattr(module, "MySQLDatabase", lambda *_args, **_kwargs: _BoomDB())
    res = _run_case({**req_base, "db_type": "mysql"})
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "connect boom" in res["message"]