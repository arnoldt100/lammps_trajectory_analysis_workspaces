import json
from dataclasses import replace
from pathlib import Path

import pytest

from lammps_trajectory_analysis_workspaces.file_parser import (
    FileParserOptions,
    json_file_parser,
)


def test_render_template_generates_expected_slurm_text():
    template = (
        "#!/bin/bash\n"
        "#SBATCH --job-name=__JOB_NAME__\n"
        "#SBATCH --time=__WALLTIME__\n"
        'echo "__JOB_NAME__"\n'
    )
    replacements = {"__JOB_NAME__": "analysis", "__WALLTIME__": "01:00:00"}

    assert json_file_parser._render_template(template, json.dumps(replacements)) == (
        "#!/bin/bash\n"
        "#SBATCH --job-name=analysis\n"
        "#SBATCH --time=01:00:00\n"
        'echo "analysis"\n'
    )


def test_render_template_accepts_data_assignment_with_named_keys():
    json_text = """data = {
  "jobname": "PC-9-ar_small_box",
  "walltime": "00:05:00","batch_queue": "batch",
  "number_nodes": "1",
  "number_cores": "1"
}"""
    template = (
        "__jobname__ __walltime__ __batch_queue__ "
        "__number_nodes__ __number_cores__ __jobname__"
    )

    assert json_file_parser._render_template(template, json_text) == (
        "PC-9-ar_small_box 00:05:00 batch 1 1 PC-9-ar_small_box"
    )


@pytest.mark.parametrize("prefix", ["data=", "  data  = \n", "\ndata\t=\t"])
def test_render_template_accepts_assignment_whitespace(prefix):
    assert json_file_parser._render_template("__jobname__", prefix + '{"jobname": "x"}') == "x"


@pytest.mark.parametrize(
    "json_text",
    [
        'other = {"jobname": "x"}',
        'data == {"jobname": "x"}',
        'data = {"jobname": "x"}; print("not executed")',
        "data = {'jobname': 'x'}",
        'data = {"jobname": "x",}',
    ],
)
def test_render_template_rejects_non_json_assignment(json_text):
    with pytest.raises(json.JSONDecodeError):
        json_file_parser._render_template("__jobname__", json_text)


def test_render_template_rejects_assignment_non_object_and_non_string_value():
    with pytest.raises(ValueError, match="JSON replacements must be an object"):
        json_file_parser._render_template("", "data = []")
    with pytest.raises(ValueError, match="must be a string"):
        json_file_parser._render_template("", 'data = {"jobname": 1}')


@pytest.mark.parametrize("key", ["", "bad__name", "bad\nname", "bad_"])
def test_render_template_rejects_invalid_assignment_keys(key):
    with pytest.raises(ValueError, match="Invalid placeholder key"):
        json_file_parser._render_template("", "data = " + json.dumps({key: "x"}))


def test_render_template_assignment_keys_are_case_sensitive():
    with pytest.raises(ValueError, match="Missing replacement"):
        json_file_parser._render_template("__JOBNAME__", 'data = {"jobname": "x"}')


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("__A__ __B__", "first second"),
        ("__A____B__", "firstsecond"),
        ("__A__ __A__ __B__", "first first second"),
        ("__A__\n__B__", "first\nsecond"),
        ("before __A__ after", "before first after"),
        ("__A\nB__", "__A\nB__"),
        ("__A\nB__\n__A__", "__A\nB__\nfirst"),
        ("_A_ __unfinished", "_A_ __unfinished"),
        ("no placeholders", "no placeholders"),
        ("", ""),
    ],
)
def test_render_template_matches_independent_placeholders(template, expected):
    replacements = {"__A__": "first", "__B__": "second", "__UNUSED__": "unused"}

    assert json_file_parser._render_template(
        template, json.dumps(replacements)
    ) == expected


@pytest.mark.parametrize(
    "replacement",
    [r"\1 \g<0> C:\jobs", "$HOME ${USER} $(echo test)", "", "\u03b1\u00e9", "__B__"],
)
def test_render_template_uses_literal_non_recursive_replacements(replacement):
    replacements = {"__A__": replacement, "__B__": "not substituted"}

    assert json_file_parser._render_template(
        "before __A__ after", json.dumps(replacements)
    ) == f"before {replacement} after"


def test_render_template_preserves_unicode_and_accepts_empty_placeholder():
    replacements = {"____": "\u03b2", "__\u03b1__": "\u03b3"}

    assert json_file_parser._render_template(
        "\u03b4 ____ __\u03b1__", json.dumps(replacements)
    ) == "\u03b4 \u03b2 \u03b3"


@pytest.mark.parametrize("line_ending", ["\n", "\r\n"])
@pytest.mark.parametrize("final_newline", [False, True])
def test_render_template_preserves_line_endings(line_ending, final_newline):
    suffix = line_ending if final_newline else ""
    template = f"first __A__{line_ending}second __A__{suffix}"

    assert json_file_parser._render_template(
        template, '{"__A__": "value"}'
    ) == f"first value{line_ending}second value{suffix}"


@pytest.mark.parametrize("template", ["__MISSING__", "__A__ __MISSING__"])
def test_render_template_reports_missing_replacement(template):
    with pytest.raises(ValueError, match="Missing replacement.*__MISSING__"):
        json_file_parser._render_template(template, '{"__A__": "value"}')


def test_render_template_treats_whitespace_between_delimiters_as_placeholder():
    with pytest.raises(ValueError, match="Missing replacement for placeholder '__ __'"):
        json_file_parser._render_template("__A\nB__ __A__", '{"__A__": "value"}')


@pytest.mark.parametrize("json_text", ["", "{", '{"__A__":}', '{"__A__": "x",}'])
def test_render_template_rejects_malformed_json(json_text):
    with pytest.raises(json.JSONDecodeError):
        json_file_parser._render_template("no placeholders", json_text)


@pytest.mark.parametrize("json_text", ["[]", '["value"]', '"text"', "42", "true", "null"])
def test_render_template_requires_json_object(json_text):
    with pytest.raises(ValueError, match="JSON replacements must be an object"):
        json_file_parser._render_template("no placeholders", json_text)


@pytest.mark.parametrize(
    "key", ["", "A", "_A_", "__A", "A__", "prefix__A__", "__A__suffix", "__A\nB__"]
)
def test_render_template_rejects_invalid_keys_even_when_unused(key):
    with pytest.raises(ValueError, match="Invalid placeholder key"):
        json_file_parser._render_template("no placeholders", json.dumps({key: "value"}))


@pytest.mark.parametrize("value", [0, 1.5, True, None, [], {}])
def test_render_template_rejects_non_string_values_even_when_unused(value):
    with pytest.raises(ValueError, match="Replacement for '__A__' must be a string"):
        json_file_parser._render_template("no placeholders", json.dumps({"__A__": value}))


def test_render_template_accepts_empty_json_for_template_without_placeholders(capsys):
    assert json_file_parser._render_template("unchanged\n", "{}") == "unchanged\n"
    assert capsys.readouterr() == ("", "")


@pytest.fixture
def options(tmp_path):
    paths = FileParserOptions(
        input_file=tmp_path / "template.slurm",
        output_file=tmp_path / "batch.slurm",
        json_file=tmp_path / "replacements.json",
    )
    paths.input_file.write_bytes(b"#!/bin/bash\n#SBATCH --job-name=__JOB__\n")
    paths.json_file.write_text('{"__JOB__": "analysis"}', encoding="utf-8")
    return paths


def test_create_output_file_uses_options_without_mutation(options, capsys):
    original = replace(options)
    source_bytes = options.input_file.read_bytes(), options.json_file.read_bytes()

    assert json_file_parser.create_output_file(options) is None

    assert options.output_file.read_bytes() == (
        b"#!/bin/bash\n#SBATCH --job-name=analysis\n"
    )
    assert options == original
    assert (options.input_file.read_bytes(), options.json_file.read_bytes()) == source_bytes
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("line_ending", [b"\n", b"\r\n", b"\r"])
@pytest.mark.parametrize("final_newline", [False, True])
def test_create_output_file_preserves_line_endings(
    options, line_ending, final_newline,
):
    suffix = line_ending if final_newline else b""
    options.input_file.write_bytes(b"__JOB__" + line_ending + b"__JOB__" + suffix)

    json_file_parser.create_output_file(options)

    assert options.output_file.read_bytes() == (
        b"analysis" + line_ending + b"analysis" + suffix
    )


def test_create_output_file_preserves_mixed_endings_and_literal_unicode(options):
    options.input_file.write_bytes(b"__JOB__\r\n__JOB__\n__JOB__\r")
    value = "\u03b1 $HOME \\1 __JOB__"
    options.json_file.write_text(json.dumps({"__JOB__": value}), encoding="utf-8")

    json_file_parser.create_output_file(options)

    assert options.output_file.read_bytes() == (
        value + "\r\n" + value + "\n" + value + "\r"
    ).encode("utf-8")


def test_create_output_file_copies_template_without_placeholders(options):
    original = b"#!/bin/bash\r\necho unchanged"
    options.input_file.write_bytes(original)
    options.json_file.write_bytes(b"{}")

    json_file_parser.create_output_file(options)

    assert options.output_file.read_bytes() == original


@pytest.mark.parametrize(
    ("json_text", "error"),
    [
        ("{", json.JSONDecodeError),
        ('data = {"jobname": "x"}; pass', json.JSONDecodeError),
        ('data = {"bad__name": "x"}', ValueError),
        ('data = {"jobname": 1}', ValueError),
        ("[]", ValueError),
        ('{"JOB": "analysis"}', ValueError),
        ('{"__JOB__": 42}', ValueError),
        ("{}", ValueError),
        ('{"__JOB__": "\\ud800"}', UnicodeEncodeError),
    ],
)
@pytest.mark.parametrize("existing_output", [False, True])
def test_create_output_file_validates_before_output_creation(
    options, json_text, error, existing_output,
):
    options.json_file.write_text(json_text, encoding="utf-8")
    if existing_output:
        options.output_file.write_bytes(b"existing output")

    with pytest.raises(error):
        json_file_parser.create_output_file(options)

    if existing_output:
        assert options.output_file.read_bytes() == b"existing output"
    else:
        assert not options.output_file.exists()


@pytest.mark.parametrize("source_field", ["input_file", "json_file"])
@pytest.mark.parametrize("failure", ["missing", "directory", "invalid-utf8"])
def test_create_output_file_propagates_source_errors(options, source_field, failure):
    source = getattr(options, source_field)
    if failure == "missing":
        source.unlink()
        error = FileNotFoundError
    elif failure == "directory":
        source.unlink()
        source.mkdir()
        error = IsADirectoryError
    else:
        source.write_bytes(b"\xff")
        error = UnicodeDecodeError

    with pytest.raises(error):
        json_file_parser.create_output_file(options)

    assert not options.output_file.exists()


@pytest.mark.parametrize("source_field", ["input_file", "json_file"])
def test_create_output_file_propagates_unreadable_source(
    options, source_field, monkeypatch,
):
    source = getattr(options, source_field)
    original_read = Path.read_bytes

    def unreadable(path):
        if path == source:
            raise PermissionError("source read denied")
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", unreadable)

    with pytest.raises(PermissionError, match="source read denied"):
        json_file_parser.create_output_file(options)

    assert not options.output_file.exists()


@pytest.mark.parametrize(
    "output_kind",
    ["file", "directory", "symlink", "dangling-symlink", "input", "json"],
)
def test_create_output_file_refuses_existing_entries(options, tmp_path, output_kind):
    original_sources = options.input_file.read_bytes(), options.json_file.read_bytes()
    target = tmp_path / "target"
    target.write_bytes(b"target contents")
    if output_kind == "file":
        options.output_file.write_bytes(b"existing output")
    elif output_kind == "directory":
        options.output_file.mkdir()
    elif output_kind in ("symlink", "dangling-symlink"):
        destination = target if output_kind == "symlink" else tmp_path / "missing"
        options.output_file.symlink_to(destination)
    elif output_kind == "input":
        options.output_file = options.input_file
    else:
        options.output_file = options.json_file
    original_entry = options.output_file.lstat()

    with pytest.raises(FileExistsError):
        json_file_parser.create_output_file(options)

    assert options.output_file.lstat() == original_entry
    assert (options.input_file.read_bytes(), options.json_file.read_bytes()) == (
        original_sources
    )
    assert target.read_bytes() == b"target contents"
    if output_kind == "file":
        assert options.output_file.read_bytes() == b"existing output"


def test_create_output_file_requires_existing_parent(options, tmp_path):
    options.output_file = tmp_path / "missing" / "batch.slurm"

    with pytest.raises(FileNotFoundError):
        json_file_parser.create_output_file(options)

    assert not options.output_file.parent.exists()


def test_create_output_file_handles_output_creation_race(options, monkeypatch):
    original_open = Path.open

    def racing_open(path, mode="r", *args, **kwargs):
        if path == options.output_file and mode == "xb":
            with original_open(path, "wb") as stream:
                stream.write(b"created by another writer")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", racing_open)

    with pytest.raises(FileExistsError):
        json_file_parser.create_output_file(options)

    assert options.output_file.read_bytes() == b"created by another writer"


def test_create_output_file_propagates_output_open_failure(options, monkeypatch):
    original_open = Path.open

    def denied_open(path, mode="r", *args, **kwargs):
        if path == options.output_file and mode == "xb":
            raise PermissionError("output creation denied")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", denied_open)

    with pytest.raises(PermissionError, match="output creation denied"):
        json_file_parser.create_output_file(options)

    assert not options.output_file.exists()


@pytest.fixture
def failing_output(options, monkeypatch):
    original_open = Path.open

    def install_failure(failure):
        class FailingOutput:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def write(self, data):
                if failure == "write":
                    self.stream.write(data[:4])
                    self.stream.flush()
                    raise OSError("injected write failure")
                return self.stream.write(data)

            def __exit__(self, exc_type, exc_value, traceback):
                self.stream.close()
                if failure == "close":
                    raise OSError("injected close failure")

        def patched_open(path, mode="r", *args, **kwargs):
            stream = original_open(path, mode, *args, **kwargs)
            if path == options.output_file and mode == "xb":
                return FailingOutput(stream)
            return stream

        monkeypatch.setattr(Path, "open", patched_open)

    return install_failure


@pytest.mark.parametrize("failure", ["write", "close"])
def test_create_output_file_removes_incomplete_output(
    options, failing_output, failure,
):
    failing_output(failure)
    original_sources = options.input_file.read_bytes(), options.json_file.read_bytes()

    with pytest.raises(OSError, match=f"injected {failure} failure"):
        json_file_parser.create_output_file(options)

    assert not options.output_file.exists()
    assert (options.input_file.read_bytes(), options.json_file.read_bytes()) == (
        original_sources
    )


def test_create_output_file_reports_cleanup_failure(
    options, failing_output, monkeypatch,
):
    failing_output("write")

    def denied_unlink(path):
        assert path == options.output_file
        raise PermissionError("cleanup denied")

    monkeypatch.setattr(Path, "unlink", denied_unlink)

    with pytest.raises(OSError) as exc_info:
        json_file_parser.create_output_file(options)

    diagnostic = str(exc_info.value)
    assert "injected write failure" in diagnostic
    assert "failed to remove incomplete output" in diagnostic
    assert str(options.output_file) in diagnostic
    assert "cleanup denied" in diagnostic
    assert isinstance(exc_info.value.__cause__, PermissionError)
    assert options.output_file.read_bytes() == b"#!/b"
