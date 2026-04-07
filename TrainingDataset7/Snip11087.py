def slice_expression(self, expression, start, length):
        from django.db.models.functions import Substr

        return Substr(expression, start, length)