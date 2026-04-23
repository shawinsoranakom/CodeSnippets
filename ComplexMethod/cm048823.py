def single_listen():
            nonlocal channels
            with (
                odoo.sql_db.db_connect("postgres").cursor() as cr,
                selectors.DefaultSelector() as sel,
            ):
                cr.execute("listen imbus")
                cr.commit()
                conn = cr._cnx
                sel.register(conn, selectors.EVENT_READ)
                selector_ready_event.set()
                found = False
                while not stop_event.is_set() and not found:
                    if sel.select(timeout=5):
                        conn.poll()
                        while conn.notifies:
                            if notify_channels := [
                                c
                                for c in json.loads(conn.notifies.pop().payload)
                                if c[0] == self.env.cr.dbname
                            ]:
                                channels = notify_channels
                                found = True
                                break