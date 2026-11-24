from app.services.thinking import ThinkingSplitter


def run(chunks, prefilled=False):
    s, out = ThinkingSplitter(prefilled), []
    for c in chunks:
        out += s.feed(c)
    out += s.flush()
    merged = {"reasoning": "", "content": ""}
    for kind, text in out:
        merged[kind] += text
    return merged


def test_plain_text_passes_through():
    assert run(["Hello ", "world"]) == {"reasoning": "", "content": "Hello world"}


def test_think_block_is_separated():
    assert run(["<think>plan</think>answer"]) == {"reasoning": "plan", "content": "answer"}


def test_tags_split_across_chunks():
    r = run(["<thi", "nk>pla", "n</th", "ink>ans", "wer"])
    assert r == {"reasoning": "plan", "content": "answer"}


def test_prefilled_template_starts_inside_thought():
    assert run(["step one</think>done"], prefilled=True) == {"reasoning": "step one", "content": "done"}


def test_lone_angle_bracket_is_not_swallowed():
    assert run(["a < b and ", "c <", " d"])["content"] == "a < b and c < d"
