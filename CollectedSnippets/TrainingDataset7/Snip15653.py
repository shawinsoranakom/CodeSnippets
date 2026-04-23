def run_manage(self, args, settings_file=None, manage_py=None):
        template_manage_py = (
            os.path.join(os.path.dirname(__file__), manage_py)
            if manage_py
            else os.path.join(
                os.path.dirname(conf.__file__), "project_template", "manage.py-tpl"
            )
        )
        test_manage_py = os.path.join(self.test_dir, "manage.py")
        shutil.copyfile(template_manage_py, test_manage_py)

        with open(test_manage_py) as fp:
            manage_py_contents = fp.read()
        manage_py_contents = manage_py_contents.replace(
            "{{ project_name }}", "test_project"
        )
        with open(test_manage_py, "w") as fp:
            fp.write(manage_py_contents)

        return self.run_test(["./manage.py", *args], settings_file)