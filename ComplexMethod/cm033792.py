def _find_module_utils(self):
        linenos = []
        found_basic = False
        for child in self.ast.body:
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                names = []
                try:
                    names.append(child.module)
                    if child.module.endswith('.basic'):
                        found_basic = True
                except AttributeError:
                    pass
                names.extend([n.name for n in child.names])

                if [n for n in names if n.startswith('ansible.module_utils')]:
                    linenos.append(child.lineno)

                    for name in child.names:
                        if ('module_utils' in getattr(child, 'module', '') and
                                isinstance(name, ast.alias) and
                                name.name == '*'):
                            msg = (
                                'module-utils-specific-import',
                                ('module_utils imports should import specific '
                                 'components, not "*"')
                            )
                            if self._is_new_module():
                                self.reporter.error(
                                    path=self.object_path,
                                    code=msg[0],
                                    msg=msg[1],
                                    line=child.lineno
                                )
                            else:
                                self.reporter.warning(
                                    path=self.object_path,
                                    code=msg[0],
                                    msg=msg[1],
                                    line=child.lineno
                                )

                        if (isinstance(name, ast.alias) and
                                name.name == 'basic'):
                            found_basic = True

        if not found_basic:
            self.reporter.warning(
                path=self.object_path,
                code='missing-module-utils-basic-import',
                msg='Did not find "ansible.module_utils.basic" import'
            )

        return linenos