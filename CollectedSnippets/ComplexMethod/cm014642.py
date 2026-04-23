def filtered_args(
        self,
        positional: bool = True,
        keyword: bool = True,
        values: bool = True,
        scalars: bool = True,
        generator: bool = True,
    ) -> list[LazyArgument]:
        # This function maintains the sorted order of arguments but provides different filtered views.
        # Some parts of the code care about kwargs vs args (TS lowerings),
        # other parts care about whether they need to wrap the arg in a lazy value or leave it alone.
        # Generators are special cased, as they are needed for fallback/shape-inference but not supported
        # in TS lowerings and therefore also omitted from lazy IR.
        args: list[LazyArgument] = []
        if positional:
            args.extend(self.positional_args)
        if keyword:
            args.extend(self.keyword_args)

        if values and scalars and generator:
            return args
        elif values and scalars:
            return [a for a in args if not a.is_generator]
        elif values:
            return [a for a in args if a.is_lazy_value]
        elif scalars:
            return [
                a
                for a in args
                if not a.is_lazy_value and (generator or not a.is_generator)
            ]

        return []