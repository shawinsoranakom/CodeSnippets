def test_close_connection(self):
        """
        Connection can be closed (even when not explicitly opened)
        """
        conn = mail.get_connection(username="", password="")
        conn.close()