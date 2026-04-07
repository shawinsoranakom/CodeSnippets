def get_plural(self):
        plural = self._plural_string
        if plural is not None:
            # This should be a compiled function of a typical plural-form:
            # Plural-Forms: nplurals=3; plural=n%10==1 && n%100!=11 ? 0 :
            #               n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20)
            #               ? 1 : 2;
            plural = [
                el.strip()
                for el in plural.split(";")
                if el.strip().startswith("plural=")
            ][0].split("=", 1)[1]
        return plural