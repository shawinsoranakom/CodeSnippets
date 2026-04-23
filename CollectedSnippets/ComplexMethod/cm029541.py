def update(self, result):
        """Notify Update.

        Will print the query result to the standard output.

        Keyword Arguments:
        self                   -- This object.
        result                 -- Object of type QueryResult() containing
                                  results for this query.

        Return Value:
        Nothing.
        """
        self.result = result

        response_time_text = ""
        if self.result.query_time is not None and self.verbose is True:
            response_time_text = f" [{round(self.result.query_time * 1000)}ms]"

        # Output to the terminal is desired.
        if result.status == QueryStatus.CLAIMED:
            self.countResults()
            print(Style.BRIGHT + Fore.WHITE + "[" +
                  Fore.GREEN + "+" +
                  Fore.WHITE + "]" +
                  response_time_text +
                  Fore.GREEN +
                  f" {self.result.site_name}: " +
                  Style.RESET_ALL +
                  f"{self.result.site_url_user}")
            if self.browse:
                webbrowser.open(self.result.site_url_user, 2)

        elif result.status == QueryStatus.AVAILABLE:
            if self.print_all:
                print(Style.BRIGHT + Fore.WHITE + "[" +
                      Fore.RED + "-" +
                      Fore.WHITE + "]" +
                      response_time_text +
                      Fore.GREEN + f" {self.result.site_name}:" +
                      Fore.YELLOW + " Not Found!")

        elif result.status == QueryStatus.UNKNOWN:
            if self.print_all:
                print(Style.BRIGHT + Fore.WHITE + "[" +
                      Fore.RED + "-" +
                      Fore.WHITE + "]" +
                      Fore.GREEN + f" {self.result.site_name}:" +
                      Fore.RED + f" {self.result.context}" +
                      Fore.YELLOW + " ")

        elif result.status == QueryStatus.ILLEGAL:
            if self.print_all:
                msg = "Illegal Username Format For This Site!"
                print(Style.BRIGHT + Fore.WHITE + "[" +
                      Fore.RED + "-" +
                      Fore.WHITE + "]" +
                      Fore.GREEN + f" {self.result.site_name}:" +
                      Fore.YELLOW + f" {msg}")

        elif result.status == QueryStatus.WAF:
            if self.print_all:
                print(Style.BRIGHT + Fore.WHITE + "[" +
                      Fore.RED + "-" +
                      Fore.WHITE + "]" +
                      Fore.GREEN + f" {self.result.site_name}:" +
                      Fore.RED + " Blocked by bot detection" +
                      Fore.YELLOW + " (proxy may help)")

        else:
            # It should be impossible to ever get here...
            raise ValueError(
                f"Unknown Query Status '{result.status}' for site '{self.result.site_name}'"
            )