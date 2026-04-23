def clean(self):
        url = self.cleaned_data.get("url")
        sites = self.cleaned_data.get("sites")

        same_url = FlatPage.objects.filter(url=url)
        if self.instance.pk:
            same_url = same_url.exclude(pk=self.instance.pk)

        if sites and same_url.filter(sites__in=sites).exists():
            for site in sites:
                if same_url.filter(sites=site).exists():
                    raise ValidationError(
                        _("Flatpage with url %(url)s already exists for site %(site)s"),
                        code="duplicate_url",
                        params={"url": url, "site": site},
                    )

        return super().clean()