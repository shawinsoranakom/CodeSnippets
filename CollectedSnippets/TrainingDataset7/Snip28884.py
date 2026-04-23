def has_custom_permission(self, request):
                return request.user.has_perm("%s.custom_band" % self.opts.app_label)