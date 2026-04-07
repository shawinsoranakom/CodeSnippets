def register_tzloader(tz, context):
        class SpecificTzLoader(BaseTzLoader):
            timezone = tz

        context.adapters.register_loader("timestamptz", SpecificTzLoader)