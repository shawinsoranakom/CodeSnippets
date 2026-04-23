def _check_activated(self, auto_resolve=True):
        """Check if streamlit is activated.

        Used by `streamlit run script.py`
        """
        try:
            self.load(auto_resolve)
        except (Exception, RuntimeError) as e:
            _exit(str(e))

        if self.activation is None or not self.activation.is_valid:
            _exit("Activation email not valid.")