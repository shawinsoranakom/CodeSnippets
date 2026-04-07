def assertNotUsesCursor(self, queryset):
        self.assertUsesCursor(queryset, num_expected=0)