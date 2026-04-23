def __init__(self, *args, **kwargs):
        kwargs["name"] = "_order"
        kwargs["editable"] = False
        super().__init__(*args, **kwargs)