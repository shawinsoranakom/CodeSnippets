def test_proxy_model(self):
        class Reporter(Model):
            pass

        class ProxyJournalist(Reporter):
            class Meta:
                proxy = True

        class Article(Model):
            reporter = ForeignKey(ProxyJournalist, on_delete=CASCADE)

        class ArticleInline(admin.TabularInline):
            model = Article

        class ReporterAdmin(admin.ModelAdmin):
            inlines = [ArticleInline]

        self.assertIsValid(ReporterAdmin, Reporter)