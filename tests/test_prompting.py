import pytest

from app.core.errors import AppError
from app.services.prompting import fit_context, render_template

count = lambda s: len(s.split())


def test_template_fills_input_and_variables():
    assert render_template("Translate to {{lang}}: {{input}}", "hi", {"lang": "Arabic"}) == "Translate to Arabic: hi"


def test_template_reports_missing_variables():
    with pytest.raises(AppError) as exc:
        render_template("{{input}} {{tone}}", "x", {})
    assert exc.value.code == "missing_variables"


def test_empty_template_returns_input():
    assert render_template("", "raw", {}) == "raw"


def test_fit_context_drops_oldest_and_keeps_system():
    system = {"role": "system", "content": "be brief"}
    history = [{"role": "user", "content": "one two three four five"},
               {"role": "assistant", "content": "six seven eight nine ten"},
               {"role": "user", "content": "latest question here"}]
    kept, dropped = fit_context(system, history, count, budget=30)
    assert kept[0] == system and kept[-1]["content"] == "latest question here"
    assert dropped == 2 and kept[1]["role"] == "user"


def test_fit_context_rejects_oversized_newest_message():
    with pytest.raises(AppError):
        fit_context(None, [{"role": "user", "content": "word " * 100}], count, budget=20)
