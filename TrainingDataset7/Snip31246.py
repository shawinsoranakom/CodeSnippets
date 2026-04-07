def no_available_apps(cls):
        raise Exception(
            "Please define available_apps in TransactionTestCase and its subclasses."
        )