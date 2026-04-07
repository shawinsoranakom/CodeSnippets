def get_form(self, request, obj=None, **kwargs):
        class ExtraFieldForm(SongForm):
            name = forms.CharField(max_length=50)

        return ExtraFieldForm