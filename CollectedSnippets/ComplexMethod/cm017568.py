def get_context_data(self, **kwargs):
        template = self.kwargs["template"]
        templates = []
        try:
            default_engine = Engine.get_default()
        except ImproperlyConfigured:
            # Non-trivial TEMPLATES settings aren't supported (#24125).
            pass
        else:
            directories = list(default_engine.dirs)
            for loader in default_engine.template_loaders:
                if hasattr(loader, "get_dirs"):
                    for dir_ in loader.get_dirs():
                        if dir_ not in directories:
                            directories.append(dir_)
            for index, directory in enumerate(directories):
                template_file = Path(safe_join(directory, template))
                if template_file.exists():
                    template_contents = template_file.read_text()
                else:
                    template_contents = ""
                templates.append(
                    {
                        "file": template_file,
                        "exists": template_file.exists(),
                        "contents": template_contents,
                        "order": index,
                    }
                )
        return super().get_context_data(
            **{
                **kwargs,
                "name": template,
                "templates": templates,
            }
        )