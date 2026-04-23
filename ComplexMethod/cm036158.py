def mock_decode(ids):
            # Context decodes
            if ids == [2]:
                return " term"
            if ids == [1, 2]:
                return " the term"
            if ids == [3]:
                return "\ufffd"
            if ids == [2, 3]:
                return " term\ufffd"
            if ids == [1, 2, 3]:
                return " the term\ufffd"
            # Token 4 with context [2, 3] -> completes left curly quote
            if ids == [3, 4]:
                return "\u201c"
            if ids == [2, 3, 4]:
                return " term\u201c"
            # Context for right curly quote
            if ids == [7]:
                return "ized"
            if ids == [7, 8]:
                return "ized\ufffd"
            if ids == [8, 9]:
                return "\u201d"
            if ids == [7, 8, 9]:
                return "ized\u201d"
            return "normal_text"