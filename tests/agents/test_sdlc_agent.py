import json
import pytest
from unittest.mock import MagicMock, patch
from agents.sdlc_agent import SDLCAgent


PLAN_RESPONSE = '```json\n[{"task": "setup", "description": "Create project structure"}]\n```'
CODE_RESPONSE = '```json\n{"src/app.py": "def hello():\\n    return \'hello\'"}\n```'
TEST_RESPONSE = '```json\n{"tests/test_app.py": "from src.app import hello\\ndef test_hello():\\n    assert hello() == \'hello\'"}\n```'


@pytest.fixture
def agent():
    with patch("agents.sdlc_agent.anthropic.Anthropic"):
        a = SDLCAgent("fake-key", "claude-opus-4-7")
        a._client = MagicMock()
        return a


def _mock_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def test_plan_returns_list_of_dicts(agent):
    agent._client.messages.create.return_value = _mock_response(PLAN_RESPONSE)
    result = agent.plan("As a user I want a hello endpoint")
    assert isinstance(result, list)
    assert result[0]["task"] == "setup"
    assert result[0]["description"] == "Create project structure"


def test_plan_includes_rejection_feedback_in_prompt(agent):
    agent._client.messages.create.return_value = _mock_response(PLAN_RESPONSE)
    agent.plan("story", rejection_feedback="too vague")
    call_kwargs = agent._client.messages.create.call_args
    user_content = call_kwargs[1]["messages"][0]["content"]
    assert "too vague" in user_content


def test_plan_no_feedback_omits_feedback_section(agent):
    agent._client.messages.create.return_value = _mock_response(PLAN_RESPONSE)
    agent.plan("story", rejection_feedback="")
    call_kwargs = agent._client.messages.create.call_args
    user_content = call_kwargs[1]["messages"][0]["content"]
    assert "rejection" not in user_content.lower()


def test_code_returns_dict_of_files(agent):
    agent._client.messages.create.return_value = _mock_response(CODE_RESPONSE)
    tasks = [{"task": "setup", "description": "Create project structure"}]
    result = agent.code("story", tasks)
    assert "src/app.py" in result
    assert "def hello" in result["src/app.py"]


def test_test_returns_dict_of_test_files(agent):
    agent._client.messages.create.return_value = _mock_response(TEST_RESPONSE)
    code = {"src/app.py": "def hello():\n    return 'hello'"}
    result = agent.test("story", code)
    assert "tests/test_app.py" in result


def test_test_includes_coverage_feedback_in_prompt(agent):
    agent._client.messages.create.return_value = _mock_response(TEST_RESPONSE)
    agent.test("story", {}, coverage_feedback="TOTAL 10 5 50%")
    call_kwargs = agent._client.messages.create.call_args
    user_content = call_kwargs[1]["messages"][0]["content"]
    assert "TOTAL 10 5 50%" in user_content


def test_measure_coverage_returns_float_and_report(agent, tmp_path):
    code_files = {"src/app.py": "def hello():\n    return 'hello'\n"}
    test_files = {
        "tests/__init__.py": "",
        "tests/test_app.py": (
            "import sys, os\n"
            "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))\n"
            "from src.app import hello\n"
            "def test_hello():\n"
            "    assert hello() == 'hello'\n"
        ),
    }
    coverage, report = agent.measure_coverage(code_files, test_files)
    assert isinstance(coverage, float)
    assert isinstance(report, str)


def test_measure_coverage_returns_zero_on_no_tests(agent):
    coverage, report = agent.measure_coverage({"src/app.py": "x = 1"}, {})
    assert coverage == 0.0
