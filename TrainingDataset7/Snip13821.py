def clear_routers_cache(*, setting, **kwargs):
    if setting == "DATABASE_ROUTERS":
        router.routers = ConnectionRouter().routers