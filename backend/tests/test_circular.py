"""Tests for Milestone 6 circular import detection."""

from analyzer import detect_circular_imports


def test_detects_simple_cycle_and_formats_description():
    result = detect_circular_imports({"a.py": ["b.py"], "b.py": ["a.py"]})

    assert result == [{
        "cycle": ["a.py", "b.py", "a.py"],
        "description": "a.py → b.py → a.py",
    }]


def test_detects_long_cycle():
    result = detect_circular_imports({
        "a.py": ["b.py"],
        "b.py": ["c.py"],
        "c.py": ["a.py"],
    })

    assert result[0]["cycle"] == ["a.py", "b.py", "c.py", "a.py"]
    assert result[0]["description"] == "a.py → b.py → c.py → a.py"


def test_detects_self_import():
    result = detect_circular_imports({"self.py": ["self.py"]})

    assert result == [{
        "cycle": ["self.py", "self.py"],
        "description": "self.py → self.py",
    }]


def test_acyclic_and_empty_graphs_have_no_cycles():
    assert detect_circular_imports({
        "a.py": ["b.py"],
        "b.py": [],
        "isolated.py": [],
    }) == []
    assert detect_circular_imports({}) == []


def test_disconnected_components_are_checked_independently():
    result = detect_circular_imports({
        "a.py": ["b.py"],
        "b.py": ["a.py"],
        "c.py": ["d.py"],
        "d.py": ["e.py"],
        "e.py": ["c.py"],
        "leaf.py": [],
    })

    assert [item["cycle"] for item in result] == [
        ["a.py", "b.py", "a.py"],
        ["c.py", "d.py", "e.py", "c.py"],
    ]


def test_rotated_paths_and_duplicate_edges_do_not_duplicate_cycles():
    result = detect_circular_imports({
        "a.py": ["b.py", "b.py"],
        "b.py": ["c.py"],
        "c.py": ["a.py"],
    })

    assert len(result) == 1
    assert result[0]["cycle"] == ["a.py", "b.py", "c.py", "a.py"]
