def get(self, contact=None, limit=10, substring=None):
        if sys.platform.lower() != "darwin":
            print("Only supported on Mac.")
            return
        if not self.can_access_database():
            self.prompt_full_disk_access()

        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # Set row factory
        cursor = conn.cursor()
        query = """
SELECT message.*, handle.id as sender FROM message
LEFT JOIN handle ON message.handle_id = handle.ROWID
        """
        params = []
        conditions = []

        if contact:
            conditions.append("handle.id=?")
            params.append(contact)
        if substring:
            conditions.append("message.text LIKE ?")
            params.append(f"%{substring}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY message.date DESC"

        cursor.execute(query, params)

        # Parse plist data and make messages readable
        readable_messages = []
        while len(readable_messages) < limit:
            try:
                message = cursor.fetchone()
                if message is None:
                    break
                message_dict = dict(message)  # Convert row to dictionary
                text_data = message_dict.get("text")
                if text_data:
                    try:
                        # Try to parse as plist
                        plist_data = plistlib.loads(text_data)
                        text = plist_data.get("NS.string", "")
                    except:
                        # If plist parsing fails, use the raw string
                        text = text_data
                    if text:  # Only add messages with content
                        # Convert Apple timestamp to datetime
                        date = datetime.datetime(2001, 1, 1) + datetime.timedelta(
                            seconds=message_dict.get("date") / 10**9
                        )
                        sender = message_dict.get("sender")
                        if message_dict.get("is_from_me") == 1:
                            sender = "(Me)"
                        readable_messages.append(
                            {"date": date, "from": sender, "text": text}
                        )
            except sqlite3.Error as e:
                break

        conn.close()
        return readable_messages