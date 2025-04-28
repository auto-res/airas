from unittest.mock import patch, MagicMock
from airas.retrieve_paper_subgraph.nodes.extract_github_url_node import (
    ExtractGithubUrlNode,
)


# Normal case test: returns correct GitHub URL from text and LLM
@patch(
    "airas.retrieve_paper_subgraph.nodes.extract_github_url_node.vertexai_client",
    return_value={"index": 0},
)
@patch(
    "airas.retrieve_paper_subgraph.nodes.extract_github_url_node.requests.get",
    return_value=MagicMock(status_code=200, raise_for_status=lambda: None),
)
def test_extract_github_url_success(mock_requests, mock_vertexai):
    node = ExtractGithubUrlNode(llm_name="dummy-llm")
    text = "Check this repo: https://github.com/user/repo"
    summary = "summary"
    result = node.execute(text, summary)
    assert result == "https://github.com/user/repo"


# Abnormal case test: returns empty string if no valid GitHub URL
@patch(
    "airas.retrieve_paper_subgraph.nodes.extract_github_url_node.vertexai_client",
    return_value=None,
)
@patch(
    "airas.retrieve_paper_subgraph.nodes.extract_github_url_node.requests.get",
    return_value=MagicMock(status_code=404, raise_for_status=lambda: None),
)
def test_extract_github_url_no_url(mock_requests, mock_vertexai):
    node = ExtractGithubUrlNode(llm_name="dummy-llm")
    text = "No github url here"
    summary = "summary"
    result = node.execute(text, summary)
    assert result == ""


# Abnormal case test: returns empty string if vertexai_client returns None
@patch(
    "airas.retrieve_paper_subgraph.nodes.extract_github_url_node.vertexai_client",
    return_value=None,
)
@patch(
    "airas.retrieve_paper_subgraph.nodes.extract_github_url_node.requests.get",
    return_value=MagicMock(status_code=200, raise_for_status=lambda: None),
)
def test_extract_github_url_vertexai_none(mock_requests, mock_vertexai):
    node = ExtractGithubUrlNode(llm_name="dummy-llm")
    text = "Check this repo: https://github.com/user/repo"
    summary = "summary"
    result = node.execute(text, summary)
    assert result == ""
