def __getattribute__(self, attr):
        """Trigger the load of the module and return the attribute."""
        __spec__ = object.__getattribute__(self, '__spec__')
        loader_state = __spec__.loader_state
        with loader_state['lock']:
            # Only the first thread to get the lock should trigger the load
            # and reset the module's class. The rest can now getattr().
            if object.__getattribute__(self, '__class__') is _LazyModule:
                __class__ = loader_state['__class__']

                # Reentrant calls from the same thread must be allowed to proceed without
                # triggering the load again.
                # exec_module() and self-referential imports are the primary ways this can
                # happen, but in any case we must return something to avoid deadlock.
                if loader_state['is_loading']:
                    return __class__.__getattribute__(self, attr)
                loader_state['is_loading'] = True

                __dict__ = __class__.__getattribute__(self, '__dict__')

                # All module metadata must be gathered from __spec__ in order to avoid
                # using mutated values.
                # Get the original name to make sure no object substitution occurred
                # in sys.modules.
                original_name = __spec__.name
                # Figure out exactly what attributes were mutated between the creation
                # of the module and now.
                attrs_then = loader_state['__dict__']
                attrs_now = __dict__
                attrs_updated = {}
                for key, value in attrs_now.items():
                    # Code that set an attribute may have kept a reference to the
                    # assigned object, making identity more important than equality.
                    if key not in attrs_then:
                        attrs_updated[key] = value
                    elif id(attrs_now[key]) != id(attrs_then[key]):
                        attrs_updated[key] = value
                __spec__.loader.exec_module(self)
                # If exec_module() was used directly there is no guarantee the module
                # object was put into sys.modules.
                if original_name in sys.modules:
                    if id(self) != id(sys.modules[original_name]):
                        raise ValueError(f"module object for {original_name!r} "
                                          "substituted in sys.modules during a lazy "
                                          "load")
                # Update after loading since that's what would happen in an eager
                # loading situation.
                __dict__.update(attrs_updated)
                # Finally, stop triggering this method, if the module did not
                # already update its own __class__.
                if isinstance(self, _LazyModule):
                    object.__setattr__(self, '__class__', __class__)

        return getattr(self, attr)