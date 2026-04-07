def __init__(self):
        from django.db.models import JSONField

        super().__init__(None, output_field=JSONField())