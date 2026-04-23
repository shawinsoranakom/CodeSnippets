def handle(self, *args, **options):
        self.stdout.write("Hello, world!", self.style.ERROR)
        self.stderr.write("Hello, world!", self.style.ERROR)