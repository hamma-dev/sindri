"""Regression test: PLOT_CONTENT_TEMPLATE must be safe with >1 plot block.

Two ``type="plot"`` blocks on one page previously collided: the helper
functions/vars (``createSubplots``, ``updateSubplots``, ``unpack``,
``firstUpdate``) were emitted at page-global scope, so the second block's
``<script>`` overwrote the first's ``createSubplots`` (which bakes in
``plotLayout_{section_id}``), clobbering the first plot's render. They are
now suffixed with ``_{section_id}``.
"""
import sindri.website.templates as templates


class _Blank(dict):
    """Format mapping that blanks every field except those provided."""

    def __missing__(self, key):
        return ""


def _render(section_id):
    return templates.PLOT_CONTENT_TEMPLATE.format_map(_Blank(section_id=section_id))


def test_no_page_global_plot_helpers():
    """No bare (un-suffixed) helper defs remain in the rendered script."""
    rendered = _render("plot")
    for bare in (
            "function createSubplots(",
            "function updateSubplots(",
            "function unpack(",
            "var firstUpdate =",
            ):
        assert bare not in rendered, f"page-global symbol still present: {bare}"


def test_two_blocks_do_not_collide():
    """Two plot blocks emit distinct, non-overlapping helper symbols."""
    both = _render("plot") + _render("noise")
    for name in ("createSubplots", "updateSubplots", "unpack"):
        assert both.count(f"function {name}_plot(") == 1
        assert both.count(f"function {name}_noise(") == 1
        assert f"function {name}(" not in both
    assert "var firstUpdate_plot = true;" in both
    assert "var firstUpdate_noise = true;" in both


def test_callers_use_section_scoped_helpers():
    """The XHR callback calls the section-scoped helpers, not globals."""
    rendered = _render("noise")
    assert 'createSubplots_noise("noise-output"' in rendered
    assert 'updateSubplots_noise("noise-output"' in rendered
    assert "if (firstUpdate_noise)" in rendered
    assert "firstUpdate_noise = false;" in rendered


def test_template_still_formats():
    """The template formats without raising (no stray/unescaped braces)."""
    rendered = _render("anything")
    assert "createSubplots_anything" in rendered
