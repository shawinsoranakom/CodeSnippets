def import_options(cls, browser):
        return import_string("selenium.webdriver.%s.options.Options" % browser)