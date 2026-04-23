def visit_ImportFrom(self, node):
        """
        Handle from ansible.module_utils.MODLIB import [.MODLIBn] [as asname]

        Also has to handle relative imports.

        We save these as interesting submodules when the imported library is in ansible.module_utils
        or ansible.collections.

        If the module imports `ansible.module_utils.embed`, assignment analysis is enabled for static resource embedding via EmbedManager.embed().
        """
        # FIXME: These should all get skipped:
        # from ansible.executor import module_common
        # from ...executor import module_common
        # from ... import executor (Currently it gives a non-helpful error)

        depth = self._depth
        module_fqn = self.module_fqn
        submodules_add = self.submodules.add
        optional_imports_add = self.optional_imports.add

        node_level = node.level
        module = node.module

        if node_level > 0:
            # if we're in a package init, we have to add one to the node level (and make it none if 0 to preserve the right slicing behavior)
            level_slice_offset = -node_level + 1 or None if self.is_pkg_init else -node_level
            if module_fqn:
                parts = tuple(module_fqn.split('.'))
                if module:
                    # relative import: from .module import x
                    node_module = '.'.join(parts[:level_slice_offset] + (module,))
                else:
                    # relative import: from . import x
                    node_module = '.'.join(parts[:level_slice_offset])
            else:
                # fall back to an absolute import
                node_module = module
        else:
            # absolute import: from module import x
            node_module = module

        # Specialcase: six is a special case because of its
        # import logic
        py_mod = None
        if node.names[0].name == '_six':
            submodules_add(('_six',))
        elif node_module.startswith('ansible.module_utils'):
            # from ansible.module_utils.MODULE1[.MODULEn] import IDENTIFIER [as asname]
            # from ansible.module_utils.MODULE1[.MODULEn] import MODULEn+1 [as asname]
            # from ansible.module_utils.MODULE1[.MODULEn] import MODULEn+1 [,IDENTIFIER] [as asname]
            # from ansible.module_utils import MODULE1 [,MODULEn] [as asname]
            py_mod = tuple(node_module.split('.'))

        elif node_module.startswith('ansible_collections.'):
            if node_module.endswith('plugins.module_utils') or '.plugins.module_utils.' in node_module:
                # from ansible_collections.ns.coll.plugins.module_utils import MODULE [as aname] [,MODULE2] [as aname]
                # from ansible_collections.ns.coll.plugins.module_utils.MODULE import IDENTIFIER [as aname]
                # FIXME: Unhandled cornercase (needs to be ignored):
                # from ansible_collections.ns.coll.plugins.[!module_utils].[FOO].plugins.module_utils import IDENTIFIER
                py_mod = tuple(node_module.split('.'))
            else:
                # Not from module_utils so ignore.  for instance:
                # from ansible_collections.ns.coll.plugins.lookup import IDENTIFIER
                pass

        if py_mod:
            for alias in node.names:
                submodules_add(a_py_mod := py_mod + (alias.name,))
                # if the import's parent is the root document, it's a required import, otherwise it's optional
                if depth:
                    optional_imports_add(a_py_mod)
                elif alias.name == 'embed' and node_module == 'ansible.module_utils':
                    self._visit_embed_import(node_module, node, alias)
                elif alias.name == 'EmbedManager' and node_module == 'ansible.module_utils.embed':
                    self._visit_embed_import(node_module, node, alias)