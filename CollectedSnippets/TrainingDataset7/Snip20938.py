def add_question_mark(func):
            def _wrapper(*args, **kwargs):
                return func(*args, **kwargs) + "?"

            return _wrapper