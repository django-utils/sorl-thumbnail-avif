import os
import re
from subprocess import PIPE, Popen

from django.template.loader import render_to_string
from django.test import Client, TestCase
from django.test.utils import override_settings
import pytest

from sorl.thumbnail.conf import settings

from .models import Item
from .utils import BaseTestCase


@pytest.mark.django_db
class TemplateTestCaseA(BaseTestCase):
    def test_model(self):
        item = Item.objects.get(image="500x500.avif")
        val = render_to_string(
            "thumbnail1.html",
            {
                "item": item,
            },
        ).strip()
        self.assertEqual(
            val, '<img style="margin:0px 0px 0px 0px" width="200" height="100">'
        )
        val = render_to_string(
            "thumbnail2.html",
            {
                "item": item,
            },
        ).strip()
        self.assertEqual(
            val, '<img style="margin:0px 50px 0px 50px" width="100" height="100">'
        )

    def test_nested(self):
        item = Item.objects.get(image="500x500.avif")
        val = render_to_string(
            "thumbnail6.html",
            {
                "item": item,
            },
        ).strip()
        self.assertEqual(
            val,
            (
                '<a href="/media/test/cache/36853685c559aded9c3e888b2a3a46cbd538.avif">'
                '<img src="/media/test/cache/de9cde9ccbf969df311687c741f0f53694e7.avif" '
                'width="400" height="400"></a>'
            ),
        )

    def test_serialization_options(self):
        item = Item.objects.get(image="500x500.avif")

        for _ in range(0, 20):
            # we could be lucky...
            val0 = render_to_string(
                "thumbnail7.html",
                {
                    "item": item,
                },
            ).strip()
            val1 = render_to_string(
                "thumbnail7a.html",
                {
                    "item": item,
                },
            ).strip()
            self.assertEqual(val0, val1)

    def test_options(self):
        item = Item.objects.get(image="500x500.avif")
        options = {
            "crop": "center",
            "upscale": True,
            "quality": 77,
        }
        val0 = render_to_string(
            "thumbnail8.html",
            {
                "item": item,
                "options": options,
            },
        ).strip()
        val1 = render_to_string(
            "thumbnail8a.html",
            {
                "item": item,
            },
        ).strip()
        self.assertEqual(val0, val1)

    def test_nonprogressive(self):
        im = Item.objects.get(image="500x500.avif").image
        th = self.BACKEND.get_thumbnail(im, "100x100", progressive=False)
        path = os.path.join(settings.MEDIA_ROOT, th.name)
        p = Popen(["identify", "-verbose", path], stdout=PIPE)
        p.wait()
        m = re.search("Interlace: None", str(p.stdout.read()))
        p.stdout.close()
        self.assertEqual(bool(m), True)


@pytest.mark.django_db
class TemplateTestCaseB(BaseTestCase):
    def test_url(self):
        val = render_to_string("thumbnail3.html", {}).strip()
        self.assertEqual(
            val, '<img style="margin:0px 0px 0px 0px" width="20" height="20">'
        )

    def test_portrait(self):
        val = render_to_string(
            "thumbnail4.html",
            {
                "source": "https://dummyimage.com/120x100/",
                "dims": "x66",
            },
        ).strip()
        self.assertEqual(
            val,
            '<img src="/media/test/cache/2523252307b8dbbc9257c9ec47227adb030c.avif" '
            'width="79" height="66" class="landscape">',
        )

        val = render_to_string(
            "thumbnail4.html",
            {
                "source": "https://dummyimage.com/100x120/",
                "dims": "x66",
            },
        ).strip()
        self.assertEqual(val, '<img width="1" height="1" class="portrait">')

        with override_settings(THUMBNAIL_DEBUG=True):
            with self.assertRaises(FileNotFoundError):
                render_to_string(
                    "thumbnail4a.html",
                    {
                        "source": "broken.avif",
                    },
                ).strip()

        with override_settings(THUMBNAIL_DEBUG=False):
            val = render_to_string(
                "thumbnail4a.html",
                {
                    "source": "broken.avif",
                },
            ).strip()
            self.assertEqual(val, "no")

    def test_empty(self):
        val = render_to_string("thumbnail5.html", {}).strip()
        self.assertEqual(val, "<p>empty</p>")


class TemplateTestCaseClient(TestCase):
    def test_empty_error(self):
        with override_settings(THUMBNAIL_DEBUG=False):
            from django.core.mail import outbox

            client = Client()
            response = client.get("/thumbnail9.html")
            self.assertEqual(response.content.strip(), b"<p>empty</p>")
            self.assertEqual(outbox[0].subject, "[sorl-thumbnail] ERROR: Unknown URL")

            end = outbox[0].body.split("\n\n")[-2].split(":")[1].strip()

            self.assertEqual(end, "[Errno 2] No such file or directory")


@pytest.mark.django_db
class TemplateTestCaseTemplateTagAlias(BaseTestCase):
    """Testing alternative template tag (alias)."""

    def test_model(self):
        item = Item.objects.get(image="500x500.avif")
        val = render_to_string("thumbnail1_alias.html", {"item": item}).strip()
        self.assertEqual(
            val, '<img style="margin:0px 0px 0px 0px" width="200" height="100">'
        )
        val = render_to_string("thumbnail2_alias.html", {"item": item}).strip()
        self.assertEqual(
            val, '<img style="margin:0px 50px 0px 50px" width="100" height="100">'
        )

    def test_nested(self):
        item = Item.objects.get(image="500x500.avif")
        val = render_to_string("thumbnail6_alias.html", {"item": item}).strip()
        self.assertEqual(
            val,
            (
                '<a href="/media/test/cache/36853685c559aded9c3e888b2a3a46cbd538.avif">'
                '<img src="/media/test/cache/de9cde9ccbf969df311687c741f0f53694e7.avif" '
                'width="400" height="400"></a>'
            ),
        )

    def test_serialization_options(self):
        item = Item.objects.get(image="500x500.avif")

        for _ in range(0, 20):
            # we could be lucky...
            val0 = render_to_string(
                "thumbnail7_alias.html",
                {
                    "item": item,
                },
            ).strip()
            val1 = render_to_string(
                "thumbnail7a_alias.html",
                {
                    "item": item,
                },
            ).strip()
            self.assertEqual(val0, val1)

    def test_options(self):
        item = Item.objects.get(image="500x500.avif")
        options = {
            "crop": "center",
            "upscale": True,
            "quality": 77,
        }
        val0 = render_to_string(
            "thumbnail8_alias.html", {"item": item, "options": options}
        ).strip()
        val1 = render_to_string("thumbnail8a_alias.html", {"item": item}).strip()
        self.assertEqual(val0, val1)
