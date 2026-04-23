def domain_return_ok(self, domain, request):
        # Liberal check of.  This is here as an optimization to avoid
        # having to load lots of MSIE cookie files unless necessary.
        req_host, erhn = eff_request_host(request)
        if not req_host.startswith("."):
            req_host = "."+req_host
        if not erhn.startswith("."):
            erhn = "."+erhn
        if domain and not domain.startswith("."):
            dotdomain = "." + domain
        else:
            dotdomain = domain
        if not (req_host.endswith(dotdomain) or erhn.endswith(dotdomain)):
            #_debug("   request domain %s does not match cookie domain %s",
            #       req_host, domain)
            return False

        if self.is_blocked(domain):
            _debug("   domain %s is in user block-list", domain)
            return False
        if self.is_not_allowed(domain):
            _debug("   domain %s is not in user allow-list", domain)
            return False

        return True