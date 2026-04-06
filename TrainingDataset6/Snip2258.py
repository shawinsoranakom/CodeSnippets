def app_alias(self, alias_name):
        return """alias {0}='eval "$(TF_ALIAS={0} PYTHONIOENCODING=utf-8 """ \
               """thefuck "$(fc -ln -1)")"'""".format(alias_name)