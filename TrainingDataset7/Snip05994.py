def __init__(self, field, admin_site, attrs=None, choices=(), using=None):
        self.field = field
        self.admin_site = admin_site
        self.db = using
        self.choices = choices
        self.attrs = {} if attrs is None else attrs.copy()
        self.i18n_name = get_select2_language()