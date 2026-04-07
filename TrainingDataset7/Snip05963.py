def __init__(self, attrs=None):
        widgets = [BaseAdminDateWidget, BaseAdminTimeWidget]
        # Note that we're calling MultiWidget, not SplitDateTimeWidget, because
        # we want to define widgets.
        forms.MultiWidget.__init__(self, widgets, attrs)