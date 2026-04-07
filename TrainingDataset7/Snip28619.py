def test_inlineformset_custom_callback(self):
        callback = Callback()
        inlineformset_factory(
            User,
            UserSite,
            form=UserSiteForm,
            formfield_callback=callback,
            fields="__all__",
        )
        self.assertCallbackCalled(callback)