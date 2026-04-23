def wrapper(*args: Any, **kwargs: Any) -> Any:
                for key, arg in kwargs.items():
                    if key == "config" and (
                        isinstance(arg, dict)
                        and "configurable" in arg
                        and isinstance(arg["configurable"], dict)
                    ):
                        runnable, config = self.prepare(cast("RunnableConfig", arg))
                        kwargs = {**kwargs, "config": config}
                        return getattr(runnable, name)(*args, **kwargs)

                for idx, arg in enumerate(args):
                    if (
                        isinstance(arg, dict)
                        and "configurable" in arg
                        and isinstance(arg["configurable"], dict)
                    ):
                        runnable, config = self.prepare(cast("RunnableConfig", arg))
                        argsl = list(args)
                        argsl[idx] = config
                        return getattr(runnable, name)(*argsl, **kwargs)

                if self.config:
                    runnable, config = self.prepare()
                    return getattr(runnable, name)(*args, **kwargs)

                return attr(*args, **kwargs)