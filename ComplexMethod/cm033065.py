def validate_connector_settings(self) -> None:
        if self.github_client is None:
            raise ConnectorMissingCredentialError("GitHub credentials not loaded.")

        if not self.repo_owner:
            raise ConnectorValidationError(
                "Invalid connector settings: 'repo_owner' must be provided."
            )

        try:
            if self.repositories:
                if "," in self.repositories:
                    # Multiple repositories specified
                    repo_names = [name.strip() for name in self.repositories.split(",")]
                    if not repo_names:
                        raise ConnectorValidationError(
                            "Invalid connector settings: No valid repository names provided."
                        )

                    # Validate at least one repository exists and is accessible
                    valid_repos = False
                    validation_errors = []

                    for repo_name in repo_names:
                        if not repo_name:
                            continue

                        try:
                            test_repo = self.github_client.get_repo(
                                f"{self.repo_owner}/{repo_name}"
                            )
                            logging.info(
                                f"Successfully accessed repository: {self.repo_owner}/{repo_name}"
                            )
                            test_repo.get_contents("")
                            valid_repos = True
                            # If at least one repo is valid, we can proceed
                            break
                        except GithubException as e:
                            validation_errors.append(
                                f"Repository '{repo_name}': {e.data.get('message', str(e))}"
                            )

                    if not valid_repos:
                        error_msg = (
                            "None of the specified repositories could be accessed: "
                        )
                        error_msg += ", ".join(validation_errors)
                        raise ConnectorValidationError(error_msg)
                else:
                    # Single repository (backward compatibility)
                    test_repo = self.github_client.get_repo(
                        f"{self.repo_owner}/{self.repositories}"
                    )
                    test_repo.get_contents("")
            else:
                # Try to get organization first
                try:
                    org = self.github_client.get_organization(self.repo_owner)
                    total_count = org.get_repos().totalCount
                    if total_count == 0:
                        raise ConnectorValidationError(
                            f"Found no repos for organization: {self.repo_owner}. "
                            "Does the credential have the right scopes?"
                        )
                except GithubException as e:
                    # Check for missing SSO
                    MISSING_SSO_ERROR_MESSAGE = "You must grant your Personal Access token access to this organization".lower()
                    if MISSING_SSO_ERROR_MESSAGE in str(e).lower():
                        SSO_GUIDE_LINK = (
                            "https://docs.github.com/en/enterprise-cloud@latest/authentication/"
                            "authenticating-with-saml-single-sign-on/"
                            "authorizing-a-personal-access-token-for-use-with-saml-single-sign-on"
                        )
                        raise ConnectorValidationError(
                            f"Your GitHub token is missing authorization to access the "
                            f"`{self.repo_owner}` organization. Please follow the guide to "
                            f"authorize your token: {SSO_GUIDE_LINK}"
                        )
                    # If not an org, try as a user
                    user = self.github_client.get_user(self.repo_owner)

                    # Check if we can access any repos
                    total_count = user.get_repos().totalCount
                    if total_count == 0:
                        raise ConnectorValidationError(
                            f"Found no repos for user: {self.repo_owner}. "
                            "Does the credential have the right scopes?"
                        )

        except RateLimitExceededException:
            raise UnexpectedValidationError(
                "Validation failed due to GitHub rate-limits being exceeded. Please try again later."
            )

        except GithubException as e:
            if e.status == 401:
                raise CredentialExpiredError(
                    "GitHub credential appears to be invalid or expired (HTTP 401)."
                )
            elif e.status == 403:
                raise InsufficientPermissionsError(
                    "Your GitHub token does not have sufficient permissions for this repository (HTTP 403)."
                )
            elif e.status == 404:
                if self.repositories:
                    if "," in self.repositories:
                        raise ConnectorValidationError(
                            f"None of the specified GitHub repositories could be found for owner: {self.repo_owner}"
                        )
                    else:
                        raise ConnectorValidationError(
                            f"GitHub repository not found with name: {self.repo_owner}/{self.repositories}"
                        )
                else:
                    raise ConnectorValidationError(
                        f"GitHub user or organization not found: {self.repo_owner}"
                    )
            else:
                raise ConnectorValidationError(
                    f"Unexpected GitHub error (status={e.status}): {e.data}"
                )

        except Exception as exc:
            raise Exception(
                f"Unexpected error during GitHub settings validation: {exc}"
            )