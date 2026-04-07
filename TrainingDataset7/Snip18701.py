def get_connection():
            # copy() reuses the existing alias and as such the same pool.
            conn = new_connection.copy()
            conn.connect()
            connections.append(conn)
            return conn