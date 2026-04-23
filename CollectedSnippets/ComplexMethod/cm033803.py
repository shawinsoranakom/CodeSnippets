def _check_version_added(self, doc, existing_doc):
        deprecated = doc.get('deprecated', False)
        if deprecated:
            return

        version_added_raw = doc.get('version_added')

        try:
            collection_name = doc.get('version_added_collection')
            version_added = self._create_strict_version(
                str(version_added_raw or '0.0'),
                collection_name=collection_name)
        except ValueError as e:
            version_added = version_added_raw or '0.0'
            if self._is_new_module() or version_added != 'historical':
                # already reported during schema validation, except:
                if version_added == 'historical':
                    self.reporter.error(
                        path=self.object_path,
                        code='module-invalid-version-added',
                        msg='version_added is not a valid version number: %r. Error: %s' % (version_added, e)
                    )
                return

        if existing_doc and str(version_added_raw) != str(existing_doc.get('version_added')):
            self.reporter.error(
                path=self.object_path,
                code='module-incorrect-version-added',
                msg='version_added should be %r. Currently %r' % (existing_doc.get('version_added'), version_added_raw)
            )

        if not self._is_new_module():
            return

        should_be = '.'.join(ansible_version.split('.')[:2])
        strict_ansible_version = self._create_strict_version(should_be, collection_name='ansible.builtin')

        if (version_added < strict_ansible_version or
                strict_ansible_version < version_added):
            self.reporter.error(
                path=self.object_path,
                code='module-incorrect-version-added',
                msg='version_added should be %r. Currently %r' % (should_be, version_added_raw)
            )