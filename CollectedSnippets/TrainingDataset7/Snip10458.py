def _serialize_path(path):
        module, name = path.rsplit(".", 1)
        if module == "django.db.models":
            imports = {"from django.db import models"}
            name = "models.%s" % name
        else:
            imports = {"import %s" % module}
            name = path
        return name, imports