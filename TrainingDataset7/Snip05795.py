def media(self):
        extra = "" if settings.DEBUG else ".min"
        js = ["vendor/jquery/jquery%s.js" % extra, "jquery.init.js", "inlines.js"]
        if self.filter_vertical or self.filter_horizontal:
            js.extend(["SelectBox.js", "SelectFilter2.js"])
        return forms.Media(js=["admin/js/%s" % url for url in js])