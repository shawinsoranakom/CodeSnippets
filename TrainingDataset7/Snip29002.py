def test_proxy_model_parent(self):
        class Parent(Model):
            pass

        class ProxyChild(Parent):
            class Meta:
                proxy = True

        class ProxyProxyChild(ProxyChild):
            class Meta:
                proxy = True

        class Related(Model):
            proxy_child = ForeignKey(ProxyChild, on_delete=CASCADE)

        class InlineFkName(admin.TabularInline):
            model = Related
            fk_name = "proxy_child"

        class InlineNoFkName(admin.TabularInline):
            model = Related

        class ProxyProxyChildAdminFkName(admin.ModelAdmin):
            inlines = [InlineFkName, InlineNoFkName]

        self.assertIsValid(ProxyProxyChildAdminFkName, ProxyProxyChild)