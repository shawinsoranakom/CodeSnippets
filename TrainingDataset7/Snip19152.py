def create_table(self):
        management.call_command("createcachetable", verbosity=0)