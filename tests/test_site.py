import pytest
from checks import no_hscroll


@pytest.mark.parametrize("width", [390, 860, 1280])
def test_index_loads(page_factory, site_url, width):
    page = page_factory(width=width)
    page.goto(f"{site_url}/index.html")
    no_hscroll(page)
    assert page.errors == []
