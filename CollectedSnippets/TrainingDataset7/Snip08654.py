def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(mail, "outbox"):
            mail.outbox = []