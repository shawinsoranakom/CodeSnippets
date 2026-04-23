def quote_value(self, value):
        # The backend "mostly works" without this function and there are use
        # cases for compiling Python without the sqlite3 libraries (e.g.
        # security hardening).
        try:
            import sqlite3

            value = sqlite3.adapt(value)
        except ImportError:
            pass
        except sqlite3.ProgrammingError:
            pass
        # Manual emulation of SQLite parameter quoting
        if isinstance(value, bool):
            return str(int(value))
        elif isinstance(value, (Decimal, float, int)):
            return str(value)
        elif isinstance(value, str):
            return "'%s'" % value.replace("'", "''")
        elif value is None:
            return "NULL"
        elif isinstance(value, (bytes, bytearray, memoryview)):
            # Bytes are only allowed for BLOB fields, encoded as string
            # literals containing hexadecimal data and preceded by a single "X"
            # character.
            return "X'%s'" % value.hex()
        else:
            raise ValueError(
                "Cannot quote parameter value %r of type %s" % (value, type(value))
            )