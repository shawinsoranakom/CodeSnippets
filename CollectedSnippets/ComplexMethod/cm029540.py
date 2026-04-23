def __init__(
            self,
            data_file_path: str|None = None,
            honor_exclusions: bool = True,
            do_not_exclude: list[str] = [],
        ):
        """Create Sites Information Object.

        Contains information about all supported websites.

        Keyword Arguments:
        self                   -- This object.
        data_file_path         -- String which indicates path to data file.
                                  The file name must end in ".json".

                                  There are 3 possible formats:
                                   * Absolute File Format
                                     For example, "c:/stuff/data.json".
                                   * Relative File Format
                                     The current working directory is used
                                     as the context.
                                     For example, "data.json".
                                   * URL Format
                                     For example,
                                     "https://example.com/data.json", or
                                     "http://example.com/data.json".

                                  An exception will be thrown if the path
                                  to the data file is not in the expected
                                  format, or if there was any problem loading
                                  the file.

                                  If this option is not specified, then a
                                  default site list will be used.

        Return Value:
        Nothing.
        """

        if not data_file_path:
            # The default data file is the live data.json which is in the GitHub repo. The reason why we are using
            # this instead of the local one is so that the user has the most up-to-date data. This prevents
            # users from creating issue about false positives which has already been fixed or having outdated data
            data_file_path = MANIFEST_URL

        if data_file_path.lower().startswith("http"):
            # Reference is to a URL.
            try:
                response = requests.get(url=data_file_path, timeout=30)
            except Exception as error:
                raise FileNotFoundError(
                    f"Problem while attempting to access data file URL '{data_file_path}':  {error}"
                )

            if response.status_code != 200:
                raise FileNotFoundError(f"Bad response while accessing "
                                        f"data file URL '{data_file_path}'."
                                        )
            try:
                site_data = response.json()
            except Exception as error:
                raise ValueError(
                    f"Problem parsing json contents at '{data_file_path}':  {error}."
                )

        else:
            # Reference is to a file.
            try:
                with open(data_file_path, "r", encoding="utf-8") as file:
                    try:
                        site_data = json.load(file)
                    except Exception as error:
                        raise ValueError(
                            f"Problem parsing json contents at '{data_file_path}':  {error}."
                        )

            except FileNotFoundError:
                raise FileNotFoundError(f"Problem while attempting to access "
                                        f"data file '{data_file_path}'."
                                        )

        site_data.pop('$schema', None)

        if honor_exclusions:
            try:
                response = requests.get(url=EXCLUSIONS_URL, timeout=10)
                if response.status_code == 200:
                    exclusions = response.text.splitlines()
                    exclusions = [exclusion.strip() for exclusion in exclusions]

                    for site in do_not_exclude:
                        if site in exclusions:
                            exclusions.remove(site)

                    for exclusion in exclusions:
                        try:
                            site_data.pop(exclusion, None)
                        except KeyError:
                            pass

            except Exception:
                # If there was any problem loading the exclusions, just continue without them
                print("Warning: Could not load exclusions, continuing without them.")
                honor_exclusions = False

        self.sites = {}

        # Add all site information from the json file to internal site list.
        for site_name in site_data:
            try:

                self.sites[site_name] = \
                    SiteInformation(site_name,
                                    site_data[site_name]["urlMain"],
                                    site_data[site_name]["url"],
                                    site_data[site_name]["username_claimed"],
                                    site_data[site_name],
                                    site_data[site_name].get("isNSFW",False)

                                    )
            except KeyError as error:
                raise ValueError(
                    f"Problem parsing json contents at '{data_file_path}':  Missing attribute {error}."
                )
            except TypeError:
                print(f"Encountered TypeError parsing json contents for target '{site_name}' at {data_file_path}\nSkipping target.\n")

        return