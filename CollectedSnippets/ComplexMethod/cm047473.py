def _get_attrs(self, model_class: type[BaseModel], name: str) -> dict[str, typing.Any]:
        """ Return the field parameter attributes as a dictionary. """
        # determine all inherited field attributes
        attrs = {}
        modules: list[str] = []
        for field in self._args__.get('_base_fields__', ()):
            if not isinstance(self, type(field)):
                # 'self' overrides 'field' and their types are not compatible;
                # so we ignore all the parameters collected so far
                attrs.clear()
                modules.clear()
                continue
            attrs.update(field._args__)
            if field._module:
                modules.append(field._module)
        attrs.update(self._args__)
        if self._module:
            modules.append(self._module)

        attrs['model_name'] = model_class._name
        attrs['name'] = name
        attrs['_module'] = modules[-1] if modules else None
        # the following is faster than calling unique or using OrderedSet
        attrs['_modules'] = tuple(unique(modules) if len(modules) > 1 else modules)

        # initialize ``self`` with ``attrs``
        if name == 'state':
            # by default, `state` fields should be reset on copy
            attrs['copy'] = attrs.get('copy', False)
        if attrs.get('compute'):
            # by default, computed fields are not stored, computed in superuser
            # mode if stored, not copied (unless stored and explicitly not
            # readonly), and readonly (unless inversible)
            attrs['store'] = store = attrs.get('store', False)
            attrs['compute_sudo'] = attrs.get('compute_sudo', store)
            if not (attrs['store'] and not attrs.get('readonly', True)):
                attrs['copy'] = attrs.get('copy', False)
            attrs['readonly'] = attrs.get('readonly', not attrs.get('inverse'))
        if attrs.get('related'):
            # by default, related fields are not stored, computed in superuser
            # mode, not copied and readonly
            attrs['store'] = store = attrs.get('store', False)
            attrs['compute_sudo'] = attrs.get('compute_sudo', attrs.get('related_sudo', True))
            attrs['copy'] = attrs.get('copy', False)
            attrs['readonly'] = attrs.get('readonly', True)
        if attrs.get('precompute'):
            if not attrs.get('compute') and not attrs.get('related'):
                warnings.warn(f"precompute attribute doesn't make any sense on non computed field {self}", stacklevel=1)
                attrs['precompute'] = False
            elif not attrs.get('store'):
                warnings.warn(f"precompute attribute has no impact on non stored field {self}", stacklevel=1)
                attrs['precompute'] = False
        if attrs.get('company_dependent'):
            if attrs.get('required'):
                warnings.warn(f"company_dependent field {self} cannot be required", stacklevel=1)
            if attrs.get('translate'):
                warnings.warn(f"company_dependent field {self} cannot be translated", stacklevel=1)
            if self.type not in COMPANY_DEPENDENT_FIELDS:
                warnings.warn(f"company_dependent field {self} is not one of the allowed types {COMPANY_DEPENDENT_FIELDS}", stacklevel=1)
            attrs['copy'] = attrs.get('copy', False)
            # speed up search and on delete
            attrs['index'] = attrs.get('index', 'btree_not_null')
            attrs['prefetch'] = attrs.get('prefetch', 'company_dependent')
            attrs['_depends_context'] = ('company',)
        # parameters 'depends' and 'depends_context' are stored in attributes
        # '_depends' and '_depends_context', respectively
        if 'depends' in attrs:
            attrs['_depends'] = tuple(attrs.pop('depends'))
        if 'depends_context' in attrs:
            attrs['_depends_context'] = tuple(attrs.pop('depends_context'))

        if 'group_operator' in attrs:
            warnings.warn("Since Odoo 18, 'group_operator' is deprecated, use 'aggregator' instead", DeprecationWarning, stacklevel=2)
            attrs['aggregator'] = attrs.pop('group_operator')

        return attrs