def test_modelformset_custom_callback(self):
        callback = Callback()
        modelformset_factory(UserSite, form=UserSiteForm, formfield_callback=callback)
        self.assertCallbackCalled(callback)