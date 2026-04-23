def swappable_first_key(self, item):
        """
        Place potential swappable models first in lists of created models (only
        real way to solve #22783).
        """
        try:
            model_state = self.to_state.models[item]
            base_names = {
                base if isinstance(base, str) else base.__name__
                for base in model_state.bases
            }
            string_version = "%s.%s" % (item[0], item[1])
            if (
                model_state.options.get("swappable")
                or "AbstractUser" in base_names
                or "AbstractBaseUser" in base_names
                or settings.AUTH_USER_MODEL.lower() == string_version.lower()
            ):
                return ("___" + item[0], "___" + item[1])
        except LookupError:
            pass
        return item