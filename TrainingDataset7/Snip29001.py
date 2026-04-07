def test_proxy_model_fk_name(self):
        class ReporterFkName(Model):
            pass

        class ProxyJournalistFkName(ReporterFkName):
            class Meta:
                proxy = True

        class ArticleFkName(Model):
            reporter = ForeignKey(ProxyJournalistFkName, on_delete=CASCADE)

        class ArticleInline(admin.TabularInline):
            model = ArticleFkName
            fk_name = "reporter"

        class ReporterAdmin(admin.ModelAdmin):
            inlines = [ArticleInline]

        self.assertIsValid(ReporterAdmin, ReporterFkName)