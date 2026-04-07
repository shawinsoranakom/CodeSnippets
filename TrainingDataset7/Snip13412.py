def __repr__(self):
        return (
            "<%s:%s app_dirs=%s%s debug=%s loaders=%s string_if_invalid=%s "
            "file_charset=%s%s%s autoescape=%s>"
        ) % (
            self.__class__.__qualname__,
            "" if not self.dirs else " dirs=%s" % repr(self.dirs),
            self.app_dirs,
            (
                ""
                if not self.context_processors
                else " context_processors=%s" % repr(self.context_processors)
            ),
            self.debug,
            repr(self.loaders),
            repr(self.string_if_invalid),
            repr(self.file_charset),
            "" if not self.libraries else " libraries=%s" % repr(self.libraries),
            "" if not self.builtins else " builtins=%s" % repr(self.builtins),
            repr(self.autoescape),
        )