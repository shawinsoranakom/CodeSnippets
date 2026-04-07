def mock_send(self, s):
                smtp_messages.append(s)
                return send(self, s)