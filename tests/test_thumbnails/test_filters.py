from django.template.loader import render_to_string
import pytest

from .utils import BaseTestCase


@pytest.mark.django_db
class FilterTestCase(BaseTestCase):
    def test_html_filter(self):
        text = '<img alt="A image!" src="https://dummyimage.com/800x800" />'
        val = render_to_string(
            "htmlfilter.html",
            {
                "text": text,
            },
        ).strip()

        self.assertEqual(
            '<img alt="A image!" '
            'src="/media/test/cache/153d153d227fd3966a748e873875b2ddb3d6.avif" />',
            val,
        )

    def test_html_filter_local_url(self):
        text = '<img alt="A image!" src="/media/500x500.avif" />'
        val = render_to_string(
            "htmlfilter.html",
            {
                "text": text,
            },
        ).strip()

        self.assertEqual(
            '<img alt="A image!" '
            'src="/media/test/cache/381e381e6ab5d3717ba4e1aa723d85bcd4de.avif" />',
            val,
        )

    def test_markdown_filter(self):
        text = "![A image!](https://dummyimage.com/800x800)"
        val = render_to_string(
            "markdownfilter.html",
            {
                "text": text,
            },
        ).strip()

        self.assertEqual(
            "![A image!](/media/test/cache/153d153d227fd3966a748e873875b2ddb3d6.avif)",
            val,
        )

    def test_markdown_filter_local_url(self):
        text = "![A image!](/media/500x500.avif)"
        val = render_to_string(
            "markdownfilter.html",
            {
                "text": text,
            },
        ).strip()

        self.assertEqual(
            "![A image!](/media/test/cache/381e381e6ab5d3717ba4e1aa723d85bcd4de.avif)",
            val,
        )
