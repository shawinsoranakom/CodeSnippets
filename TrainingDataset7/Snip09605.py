def wrap_oracle_errors():
    try:
        yield
    except Database.DatabaseError as e:
        # oracledb raises a oracledb.DatabaseError exception with the
        # following attributes and values:
        #  code = 2091
        #  message = 'ORA-02091: transaction rolled back
        #            'ORA-02291: integrity constraint (TEST_DJANGOTEST.SYS
        #               _C00102056) violated - parent key not found'
        #            or:
        #            'ORA-00001: unique constraint (DJANGOTEST.DEFERRABLE_
        #               PINK_CONSTRAINT) violated
        # Convert that case to Django's IntegrityError exception.
        x = e.args[0]
        if (
            hasattr(x, "code")
            and hasattr(x, "message")
            and x.code == 2091
            and ("ORA-02291" in x.message or "ORA-00001" in x.message)
        ):
            raise IntegrityError(*tuple(e.args))
        raise