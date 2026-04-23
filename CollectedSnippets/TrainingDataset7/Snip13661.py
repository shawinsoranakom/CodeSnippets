def _ensure_redirects_not_cyclic(self, response):
        """
        Raise a RedirectCycleError if response contains too many redirects.
        """
        redirect_chain = response.redirect_chain
        if redirect_chain[-1] in redirect_chain[:-1]:
            # Check that we're not redirecting to somewhere we've already been
            # to, to prevent loops.
            raise RedirectCycleError("Redirect loop detected.", last_response=response)
        if len(redirect_chain) > 20:
            # Such a lengthy chain likely also means a loop, but one with a
            # growing path, changing view, or changing query argument. 20 is
            # the value of "network.http.redirection-limit" from Firefox.
            raise RedirectCycleError("Too many redirects.", last_response=response)