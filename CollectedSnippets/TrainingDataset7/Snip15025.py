def django_release():
        pep440ver = get_version()
        if VERSION[3:5] == ("alpha", 0) and "dev" not in pep440ver:
            return pep440ver + ".dev"
        return pep440ver