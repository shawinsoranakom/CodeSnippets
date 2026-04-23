def override_router(self):
        return override_settings(DATABASE_ROUTERS=[WriteToOtherRouter()])