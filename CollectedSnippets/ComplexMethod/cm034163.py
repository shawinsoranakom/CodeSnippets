def dump_me(self, depth=0):
        """ this is never called from production code, it is here to be used when debugging as a 'complex print' """
        if depth == 0:
            display.debug("DUMPING OBJECT ------------------------------------------------------")
        display.debug("%s- %s (%s, id=%s)" % (" " * depth, self.__class__.__name__, self, id(self)))
        if hasattr(self, '_parent') and self._parent:
            self._parent.dump_me(depth + 2)
            dep_chain = self._parent.get_dep_chain()
            if dep_chain:
                for dep in dep_chain:
                    dep.dump_me(depth + 2)
        if hasattr(self, '_play') and self._play:
            self._play.dump_me(depth + 2)