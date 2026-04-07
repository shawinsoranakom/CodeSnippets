def __init__(self, nodelist, expire_time_var, fragment_name, vary_on, cache_name):
        self.nodelist = nodelist
        self.expire_time_var = expire_time_var
        self.fragment_name = fragment_name
        self.vary_on = vary_on
        self.cache_name = cache_name