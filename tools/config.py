from dataclasses import dataclass
import yaml


@dataclass
class GitHubConfig:
    repo: str
    base_branch: str
    ci_workflow: str


@dataclass
class AnthropicConfig:
    model: str


@dataclass
class GoogleConfig:
    credentials_path: str
    spreadsheet_id: str


@dataclass
class TrackerConfig:
    sheet_name: str


@dataclass
class StoryConfig:
    id_prefix: str


@dataclass
class Config:
    github: GitHubConfig
    anthropic: AnthropicConfig
    google: GoogleConfig
    tracker: TrackerConfig
    story: StoryConfig


def load_config(path: str = "chakra.yaml") -> Config:
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config(
        github=GitHubConfig(**data["github"]),
        anthropic=AnthropicConfig(**data["anthropic"]),
        google=GoogleConfig(**data["google"]),
        tracker=TrackerConfig(**data["tracker"]),
        story=StoryConfig(**data["story"]),
    )
