def _clean_sidebar_state(driver):
    driver.execute_script("localStorage.removeItem('django.admin.navSidebarIsOpen')")