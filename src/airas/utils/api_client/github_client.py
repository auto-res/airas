import os
import requests
import logging

from airas.utils.logging_utils import setup_logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

setup_logging()
logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 10
DEFAULT_INITIAL_WAIT = 1.0

GITHUB_RETRY = retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=wait_exponential(multiplier=DEFAULT_INITIAL_WAIT),
    retry=(
        retry_if_exception_type(requests.RequestException)
        | retry_if_exception_type(RuntimeError)
    ),
    before_sleep=before_sleep_log(logger, logging.INFO),
)


class GithubClient:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.github.com"
        self.default_headers = {
            "Accept": "application/vnd.github.raw+json",
            "Authorization": f"Bearer {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        timeout: float = 10.0,
        stream: bool = False,
    ) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        hdrs = {**self.default_headers, **(headers or {})}
        return requests.get(
            url=url, headers=hdrs, params=params, timeout=timeout, stream=stream
        )

    def _post(
        self,
        path: str,
        *,
        json: dict,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
        stream: bool = False,
    ) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        hdrs = {**self.default_headers, **(headers or {})}
        return requests.post(
            url=url, headers=hdrs, json=json, timeout=timeout, stream=stream
        )

    def get_repository_content(
        self, repository_owner: str, repository_name: str, file_path: str
    ) -> str | None:
        # https://docs.github.com/ja/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
        # For public repositories, no access token is required.
        path = f"/repos/{repository_owner}/{repository_name}/contents/{file_path}"

        response = self._get(path)
        match response.status_code:
            case 200:
                return response.text
            case 302:
                self.logger.warning("Resource not found (302).")
                return None
            case 304:
                self.logger.warning("Not Modified (304).")
                return None
            case 403:
                self.logger.warning("Forbidden (403).")
                return None
            case 404:
                self.logger.warning("Resource not found (404).")
                return None
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )

    def get_a_tree(
        self, repository_owner: str, repository_name: str, tree_sha: str
    ) -> dict | None:
        # https://docs.github.com/ja/rest/git/trees?apiVersion=2022-11-28#get-a-tree
        # For public repositories, no access token is required.
        path = f"/repos/{repository_owner}/{repository_name}/git/trees/{tree_sha}"
        params = {"recursive": "true"}

        response = self._get(path, params=params)
        match response.status_code:
            case 200:
                return response.json()
            case 404:
                self.logger.warning("Resource not found (404).")
                return None
            case 409:
                self.logger.warning("Conflict (409).")
                return None
            case 422:
                self.logger.warning(
                    "Validation failed, or the endpoint has been spammed (422)."
                )
                return None
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )

    @GITHUB_RETRY
    def check_branch_existence(
        self,
        repository_owner: str,
        repository_name: str,
        branch_name: str,
        *,
        raise_if_missing: bool = False,
    ) -> str | None:
        # https://docs.github.com/ja/rest/branches/branches?apiVersion=2022-11-28#get-a-branch
        # For public repositories, no access token is required.
        path = f"/repos/{repository_owner}/{repository_name}/branches/{branch_name}"
        headers = {"Accept": "application/vnd.github+json"}

        response = self._get(path)
        match response.status_code:
            case 200:
                self.logger.info("The specified branch exists (200).")
                response = response.json()
                return response["commit"]["sha"]
            case 404:
                msg = f"Branch not found: {path} (404)."
                self.logger.info(msg)
                if raise_if_missing:
                    raise RuntimeError(msg)
                return ""
            case 301:
                raise RuntimeError(f"Moved permanently: {path} (301).")
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )

    @GITHUB_RETRY
    def check_repository_existence(
        self, repository_owner: str, repository_name: str
    ) -> bool:
        # https://docs.github.com/ja/rest/repos/repos?apiVersion=2022-11-28#get-a-repository
        # For public repositories, no access token is required.
        path = f"/repos/{repository_owner}/{repository_name}"
        headers = {"Accept": "application/vnd.github+json"}

        response = self._get(path, headers=headers)
        match response.status_code:
            case 200:
                self.logger.info("A research repository exists (200).")
                return True
            case 404:
                self.logger.info(f"Repository not found: {path} (404).")
                return False
            case 403:
                raise RuntimeError(
                    f"Access forbidden: {path} (403).\n"
                    "The requested resource has been permanently moved to a new location."
                )
            case 301:
                raise RuntimeError(
                    f"Access forbidden: {path} (301).\n"
                    "You do not have permission to access this resource."
                )
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )

    @GITHUB_RETRY
    def create_branch(
        self,
        repository_owner: str,
        repository_name: str,
        branch_name: str,
        from_sha: str,
    ) -> bool:
        path = f"/repos/{repository_owner}/{repository_name}/git/refs"
        headers = {"Accept": "application/vnd.github+json"}
        payload = {"ref": f"refs/heads/{branch_name}", "sha": from_sha}

        response = self._post(path, headers=headers, json=payload)
        match response.status_code:
            case 201:
                self.logger.info(f"Branch created (201): {branch_name}")
                return True
            case 409:
                raise RuntimeError(f"Conflict creating branch (409): {path}")
            case 422:
                error_message = response.json()
                raise RuntimeError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}\n"
                    f"Error message: {error_message}"
                )
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )

    @GITHUB_RETRY
    def fork_repository(
        self,
        repository_name: str,
        device_type: str = "cpu",
        organization: str = "",
    ) -> bool:
        if device_type == "cpu":
            source = "auto-res/cpu-repository"
        elif device_type == "gpu":
            source = "auto-res2/gpu-repository"
        else:
            raise ValueError("Invalid device type. Must be 'cpu' or 'gpu'.")

        path = f"/repos/{source}/forks"
        headers = {"Accept": "application/vnd.github+json"}
        if organization == "":
            json = {
                "name": repository_name,
                "default_branch_only": "true",
            }
        else:
            json = {
                "organization": organization,
                "name": repository_name,
                "default_branch_only": "true",
            }

        response = self._post(path, headers=headers, json=json)
        match response.status_code:
            case 202:
                self.logger.info("Fork of the repository was successful (202).")
                return True
            case 400:
                raise RuntimeError(f"Bad request (400): {path}")
            case 403:
                raise RuntimeError(f"Access forbidden (403): {path}")
            case 404:
                raise RuntimeError(f"Resource not found (404): {path}")
            case 422:
                raise RuntimeError(f"Validation failed (422): {path}")
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )
