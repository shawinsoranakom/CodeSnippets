def normalize_function_kind(self, fullname: str) -> None:
        # Fetch the method name and possibly class.
        fields = fullname.split('.')
        name = fields.pop()
        _, cls = self.clinic._module_and_class(fields)

        # Check special method requirements.
        if name in unsupported_special_methods:
            fail(f"{name!r} is a special method and cannot be converted to Argument Clinic!")
        if name == '__init__' and (self.kind is not CALLABLE or not cls):
            fail(f"{name!r} must be a normal method; got '{self.kind}'!")
        if name == '__new__' and (self.kind is not CLASS_METHOD or not cls):
            fail("'__new__' must be a class method!")
        if self.kind in {GETTER, SETTER} and not cls:
            fail("@getter and @setter must be methods")

        # Normalise self.kind.
        if name == '__new__':
            self.kind = METHOD_NEW
        elif name == '__init__':
            self.kind = METHOD_INIT