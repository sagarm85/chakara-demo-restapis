import pytest
import yaml
from tools.config import load_config, Config, GitHubConfig, AnthropicConfig, GoogleConfig, TrackerConfig, StoryConfig


VALID_YAML = """
github:
  repo: "owner/repo"
  base_branch: "main"
  ci_workflow: "ci.yml"
anthropic:
  model: "claude-opus-4-7"
google:
  credentials_path: "./credentials.json"
  spreadsheet_id: "abc123"
tracker:
  sheet_name: "Chakra Tracker"
story:
  id_prefix: "CHAKRA"
"""


def test_load_config_returns_typed_config(tmp_path):
    cfg_file = tmp_path / "chakra.yaml"
    cfg_file.write_text(VALID_YAML)
    config = load_config(str(cfg_file))
    assert isinstance(config, Config)
    assert isinstance(config.github, GitHubConfig)
    assert isinstance(config.anthropic, AnthropicConfig)
    assert isinstance(config.google, GoogleConfig)
    assert isinstance(config.tracker, TrackerConfig)
    assert isinstance(config.story, StoryConfig)


def test_load_config_values(tmp_path):
    cfg_file = tmp_path / "chakra.yaml"
    cfg_file.write_text(VALID_YAML)
    config = load_config(str(cfg_file))
    assert config.github.repo == "owner/repo"
    assert config.github.base_branch == "main"
    assert config.github.ci_workflow == "ci.yml"
    assert config.anthropic.model == "claude-opus-4-7"
    assert config.google.credentials_path == "./credentials.json"
    assert config.google.spreadsheet_id == "abc123"
    assert config.tracker.sheet_name == "Chakra Tracker"
    assert config.story.id_prefix == "CHAKRA"


def test_load_config_missing_field_raises(tmp_path):
    bad_yaml = """
github:
  repo: "owner/repo"
anthropic:
  model: "claude-opus-4-7"
"""
    cfg_file = tmp_path / "chakra.yaml"
    cfg_file.write_text(bad_yaml)
    with pytest.raises((KeyError, TypeError)):
        load_config(str(cfg_file))


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/chakra.yaml")
