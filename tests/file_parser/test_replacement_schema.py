import json

import pytest

from lammps_trajectory_analysis_workspaces.file_parser import json_file_parser


def test_assignment_validates_and_renders():
    assert json_file_parser._render_template(
        "__jobname__ __number_nodes__",
        'data = {"jobname": "PC-9-ar_small_box", "number_nodes": "1"}',
    ) == "PC-9-ar_small_box 1"
    assert json_file_parser._render_template("unchanged", "data = {}") == "unchanged"


@pytest.mark.parametrize("text", ['{"jobname": "x"}', 'other = {"jobname": "x"}', ""])
def test_assignment_prefix_is_required(text):
    with pytest.raises(ValueError, match="must start with 'data ='"):
        json_file_parser._render_template("", text)


@pytest.mark.parametrize("value", [[], "text", 42, True, None])
def test_assignment_requires_object(value):
    with pytest.raises(ValueError, match="Invalid JSON replacements"):
        json_file_parser._render_template("", "data = " + json.dumps(value))


@pytest.mark.parametrize("value", [1, 1.5, True, None, [], {}])
def test_assignment_requires_string_values(value):
    with pytest.raises(ValueError, match="Invalid JSON replacements"):
        json_file_parser._render_template("", "data = " + json.dumps({"jobname": value}))


@pytest.mark.parametrize("key", ["", "bad__name", "bad\nname", "bad_"])
def test_assignment_requires_valid_key(key):
    with pytest.raises(ValueError, match="Invalid JSON replacements"):
        json_file_parser._render_template("", "data = " + json.dumps({key: "x"}))


@pytest.mark.parametrize("text", ["data = {", 'data = {"x": "y",}', 'data = {}; pass'])
def test_assignment_requires_strict_json(text):
    with pytest.raises(json.JSONDecodeError):
        json_file_parser._render_template("", text)
