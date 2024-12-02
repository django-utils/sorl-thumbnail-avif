import os
import unittest

import pytest
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from PIL import Image
import pillow_avif  # noqa: F401

from sorl.thumbnail import default
from sorl.thumbnail.base import ThumbnailBackend
from sorl.thumbnail.conf import settings
from sorl.thumbnail.helpers import get_module_class
from sorl.thumbnail.images import ImageFile
from sorl.thumbnail.parsers import parse_geometry
from sorl.thumbnail.templatetags.thumbnail import margin

from sorl_thumbnail_avif.thumbnail.engines import AvifEngine as PILEngine

from .models import Item
from .utils import BaseTestCase


@pytest.mark.django_db
class SimpleTestCase(BaseTestCase):
    def test_simple(self):
        item = Item.objects.get(image="500x500.avif")

        t = self.BACKEND.get_thumbnail(item.image, "400x300", crop="center")

        self.assertEqual(t.x, 400)
        self.assertEqual(t.y, 300)

        t = self.BACKEND.get_thumbnail(item.image, "1200x900", crop="13% 89%")

        self.assertEqual(t.x, 1200)
        self.assertEqual(t.y, 900)

    def test_upscale(self):
        item = Item.objects.get(image="100x100.avif")

        t = self.BACKEND.get_thumbnail(item.image, "400x300", upscale=False)

        self.assertEqual(t.x, 100)
        self.assertEqual(t.y, 100)

        t = self.BACKEND.get_thumbnail(item.image, "400x300", upscale=True)

        self.assertEqual(t.x, 300)
        self.assertEqual(t.y, 300)

    def test_upscale_and_crop(self):
        item = Item.objects.get(image="200x100.avif")

        t = self.BACKEND.get_thumbnail(
            item.image, "400x300", crop="center", upscale=False
        )

        self.assertEqual(t.x, 200)
        self.assertEqual(t.y, 100)

        t = self.BACKEND.get_thumbnail(
            item.image, "400x300", crop="center", upscale=True
        )
        self.assertEqual(t.x, 400)
        self.assertEqual(t.y, 300)

    def test_crop_and_blur(self):
        item = Item.objects.get(image="200x100.avif")

        t = self.BACKEND.get_thumbnail(item.image, "100x100", crop="center", blur="3")

        self.assertEqual(t.x, 100)
        self.assertEqual(t.y, 100)

    def test_is_portrait(self):
        im = ImageFile(Item.objects.get(image="500x500.avif").image)
        th = self.BACKEND.get_thumbnail(im, "50x200", crop="center")
        self.assertEqual(th.is_portrait(), True)
        th = self.BACKEND.get_thumbnail(im, "500x2", crop="center")
        self.assertEqual(th.is_portrait(), False)

    def test_margin(self):
        im = ImageFile(Item.objects.get(image="500x500.avif").image)
        self.assertEqual(margin(im, "1000x1000"), "250px 250px 250px 250px")
        self.assertEqual(margin(im, "800x1000"), "250px 150px 250px 150px")
        self.assertEqual(margin(im, "500x500"), "0px 0px 0px 0px")
        self.assertEqual(margin(im, "500x501"), "0px 0px 1px 0px")
        self.assertEqual(margin(im, "503x500"), "0px 2px 0px 1px")
        self.assertEqual(margin(im, "300x300"), "-100px -100px -100px -100px")

    def test_storage_serialize(self):
        im = ImageFile(Item.objects.get(image="500x500.avif").image)
        self.assertEqual(
            im.serialize_storage(), "tests.test_thumbnails.storage.TestStorage"
        )
        self.assertEqual(
            ImageFile("http://www.image.avif", default.storage).serialize_storage(),
            "tests.test_thumbnails.storage.TestStorage",
        )
        self.assertEqual(
            ImageFile("getit", default_storage).serialize_storage(),
            "tests.test_thumbnails.storage.TestStorage",
        )

    def test_transparency(self):
        item, _created = self.create_image(
            "50x50_transparent.png", (50, 50), transparent=True
        )
        th = self.BACKEND.get_thumbnail(item.image, "11x11", format="PNG")
        img = Image.open(th.storage.path(th.name))
        self.assertTrue(self.is_transparent(img))

    def test_transparency_gif_to_jpeg(self):
        path = "data/animation_w_transparency.gif"
        th = self.BACKEND.get_thumbnail(path, "11x11", format="JPEG")
        img = Image.open(th.storage.path(th.name))
        self.assertFalse(self.is_transparent(img))

    @pytest.mark.django_db
    def test_image_file_deserialize(self):
        im = ImageFile(Item.objects.get(image="500x500.avif").image)
        default.kvstore.set(im)
        self.assertEqual(
            default.kvstore.get(im).serialize_storage(),
            "tests.test_thumbnails.storage.TestStorage",
        )
        im = ImageFile("https://dummyimage.com/300x300/")
        default.kvstore.set(im)
        self.assertEqual(
            default.kvstore.get(im).serialize_storage(),
            "sorl.thumbnail.images.UrlStorage",
        )

    @pytest.mark.django_db
    def test_abspath(self):
        item = Item.objects.get(image="500x500.avif")
        image = ImageFile(item.image.path)
        val = render_to_string(
            "thumbnail20.html",
            {
                "image": image,
            },
        ).strip()

        im = self.BACKEND.get_thumbnail(image, "32x32", crop="center")
        self.assertEqual('<img src="%s">' % im.url, val)

    def test_new_tag_style(self):
        item = Item.objects.get(image="500x500.avif")
        image = ImageFile(item.image.path)
        val = render_to_string(
            "thumbnail20a.html",
            {
                "image": image,
            },
        ).strip()

        im = self.BACKEND.get_thumbnail(image, "32x32", crop="center")
        self.assertEqual('<img src="%s">' % im.url, val)

    def test_relative_absolute_same_key(self):
        image = Item.objects.get(image="500x500.avif").image
        imref1 = ImageFile(image.name)
        imref2 = ImageFile(os.path.join(settings.MEDIA_ROOT, image.name))
        self.assertEqual(imref1.key, imref2.key)

        self.create_image("medialibrary.avif", (100, 100))
        image = Item.objects.get(image="medialibrary.avif").image
        imref1 = ImageFile(image.name)
        imref2 = ImageFile(os.path.join(settings.MEDIA_ROOT, image.name))
        self.assertEqual(imref1.key, imref2.key)

        self.create_image("mediaäöü.avif", (100, 100))
        image = Item.objects.get(image="mediaäöü.avif").image
        imref1 = ImageFile(image.name)
        imref2 = ImageFile(os.path.join(settings.MEDIA_ROOT, image.name))
        self.assertEqual(imref1.key, imref2.key)

    @pytest.mark.skipif(
        "AvifEngine" not in settings.THUMBNAIL_ENGINE,
        reason="RGBA is only supported in PIL",
    )
    def test_rgba_colorspace(self):
        item = Item.objects.get(image="500x500.avif")

        t = self.BACKEND.get_thumbnail(
            item.image, "100x100", colorspace="RGBA", format="AVIF"
        )
        self.assertEqual(t.x, 100)
        self.assertEqual(t.y, 100)

    @pytest.mark.django_db
    def test_falsey_file_argument(self):
        with pytest.raises(ValueError):
            self.BACKEND.get_thumbnail("", "100x100")
        with pytest.raises(ValueError):
            self.BACKEND.get_thumbnail(None, "100x100")


@pytest.mark.django_db
class CropTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        # portrait
        name = "portrait.avif"
        fn = os.path.join(settings.MEDIA_ROOT, name)
        im = Image.new("L", (100, 200))
        im.paste(255, (0, 0, 100, 100))
        im.save(fn)
        self.portrait = ImageFile(Item.objects.get_or_create(image=name)[0].image)
        self.KVSTORE.delete(self.portrait)

        # landscape
        name = "landscape.avif"
        fn = os.path.join(settings.MEDIA_ROOT, name)
        im = Image.new("L", (200, 100))
        im.paste(255, (0, 0, 100, 100))
        im.save(fn)
        self.landscape = ImageFile(Item.objects.get_or_create(image=name)[0].image)
        self.KVSTORE.delete(self.landscape)

    def test_portrait_crop(self):
        def mean_pixel(x, y):
            values = im.getpixel((x, y))
            if not isinstance(values, (tuple, list)):
                values = [values]
            return sum(values) / len(values)

        for crop in ("center", "88% 50%", "50px"):
            th = self.BACKEND.get_thumbnail(self.portrait, "100x100", crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)

            self.assertEqual(mean_pixel(50, 0), 255)
            self.assertEqual(mean_pixel(50, 45), 255)
            self.assertEqual(250 <= mean_pixel(50, 49) <= 255, True, mean_pixel(50, 49))
            self.assertEqual(mean_pixel(50, 55), 0)
            self.assertEqual(mean_pixel(50, 99), 0)

        for crop in ("top", "0%", "0px"):
            th = self.BACKEND.get_thumbnail(self.portrait, "100x100", crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)
            for x in range(0, 99, 10):
                for y in range(0, 99, 10):
                    self.assertEqual(250 < mean_pixel(x, y) <= 255, True)

        for crop in ("bottom", "100%", "100px"):
            th = self.BACKEND.get_thumbnail(self.portrait, "100x100", crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)
            for x in range(0, 99, 10):
                for y in range(0, 99, 10):
                    self.assertEqual(0 <= mean_pixel(x, y) < 5, True)

    def test_landscape_crop(self):

        def mean_pixel(x, y):
            values = im.getpixel((x, y))
            if not isinstance(values, (tuple, list)):
                values = [values]
            return sum(values) / len(values)

        for crop in ("center", "50% 200%", "50px 700px"):
            th = self.BACKEND.get_thumbnail(self.landscape, "100x100", crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)

            self.assertEqual(mean_pixel(0, 50), 255)
            self.assertEqual(254 <= mean_pixel(45, 50) <= 255, True)
            self.assertEqual(250 < mean_pixel(49, 50) <= 255, True)
            self.assertEqual(mean_pixel(55, 50), 0)
            self.assertEqual(mean_pixel(99, 50), 0)

        for crop in ("left", "0%", "0px"):
            th = self.BACKEND.get_thumbnail(self.landscape, "100x100", crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)
            for x in range(0, 99, 10):
                for y in range(0, 99, 10):
                    self.assertEqual(250 < mean_pixel(x, y) <= 255, True)

        for crop in ("right", "100%", "100px"):
            th = self.BACKEND.get_thumbnail(self.landscape, "100x100", crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)
            coords = ((x, y) for y in range(0, 99, 10) for x in range(0, 99, 10))

            for x, y in coords:
                self.assertEqual(0 <= mean_pixel(x, y) < 5, True)

    @pytest.mark.skipif(
        "AvifEngine" not in settings.THUMBNAIL_ENGINE,
        reason="the other engines fail this test",
    )
    def test_smart_crop(self):
        th = self.BACKEND.get_thumbnail("data/white_border.jpg", "32x32", crop="smart")
        self.assertEqual(th.x, 32)
        self.assertEqual(th.y, 32)

        engine = PILEngine()
        im = engine.get_image(th)
        self.assertEqual(im.size[0], 32)
        self.assertEqual(im.size[1], 32)

    def test_image_with_orientation(self):
        name = "data/aspect_test.jpg"
        item, _ = Item.objects.get_or_create(image=name)

        im = ImageFile(item.image)
        th = self.BACKEND.get_thumbnail(im, "50x50")

        # this is a 100x200 image with orientation 6 (90 degrees CW rotate)
        # the thumbnail should end up 25x50
        self.assertEqual(th.x, 25)
        self.assertEqual(th.y, 50)

    @pytest.mark.skipif(
        "AvifEngine" not in settings.THUMBNAIL_ENGINE,
        reason="the other engines fail this test",
    )
    def test_crop_image_with_icc_profile(self):
        name = "data/icc_profile_test.jpg"
        item, _ = Item.objects.get_or_create(image=name)

        im = ImageFile(item.image)
        th = self.BACKEND.get_thumbnail(im, "100x100")

        engine = PILEngine()

        self.assertEqual(
            engine.get_image(im).info.get("icc_profile"),
            engine.get_image(th).info.get("icc_profile"),
        )


# Only PIL has support for checking pixel color. convert and wand engines are both missing it,
# so we cannot test for pixel color
class CropBoxTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        # portrait
        name = "portrait.avif"
        fn = os.path.join(settings.MEDIA_ROOT, name)
        im = Image.new("L", (100, 200))
        im.paste(255, (0, 0, 100, 100))
        im.save(fn)
        self.portrait = ImageFile(Item.objects.get_or_create(image=name)[0].image)
        self.KVSTORE.delete(self.portrait)

        # landscape
        name = "landscape.avif"
        fn = os.path.join(settings.MEDIA_ROOT, name)
        im = Image.new("L", (200, 100))
        im.paste(255, (0, 0, 100, 100))
        im.save(fn)
        self.landscape = ImageFile(Item.objects.get_or_create(image=name)[0].image)
        self.KVSTORE.delete(self.landscape)

    @pytest.mark.skipif(
        "AvifEngine" not in settings.THUMBNAIL_ENGINE,
        "the other engines fail this test",
    )
    def PIL_test_portrait_crop(self):
        def mean_pixel(x, y):
            values = im.getpixel((x, y))
            if not isinstance(values, (tuple, list)):
                values = [values]
            return sum(values) / len(values)

        # Center Crop
        th = self.BACKEND.get_thumbnail(
            self.portrait, "100x100", cropbox="0,50,100,150"
        )
        engine = PILEngine()
        im = engine.get_image(th)

        # Top half should be color, bottom not
        self.assertEqual(mean_pixel(0, 0), 255)
        self.assertEqual(mean_pixel(50, 0), 255)
        self.assertEqual(mean_pixel(50, 45), 255)
        self.assertEqual(mean_pixel(50, 55), 0)
        self.assertEqual(mean_pixel(50, 99), 0)

        # Top Crop
        th = self.BACKEND.get_thumbnail(self.portrait, "100x100", cropbox="0,0,100,100")
        engine = PILEngine()
        im = engine.get_image(th)
        for x in range(0, 99, 10):
            for y in range(0, 99, 10):
                self.assertEqual(250 < mean_pixel(x, y) <= 255, True)

        # Bottom Crop
        th = self.BACKEND.get_thumbnail(
            self.portrait, "100x100", cropbox="0,100,100,200"
        )
        engine = PILEngine()
        im = engine.get_image(th)
        for x in range(0, 99, 10):
            for y in range(0, 99, 10):
                self.assertEqual(0 <= mean_pixel(x, y) < 5, True)

    @pytest.mark.skipif(
        "AvifEngine" not in settings.THUMBNAIL_ENGINE,
        "the other engines fail this test",
    )
    def PIL_test_landscape_crop(self):

        def mean_pixel(x, y):
            values = im.getpixel((x, y))
            if not isinstance(values, (tuple, list)):
                values = [values]
            return sum(values) / len(values)

        # Center
        th = self.BACKEND.get_thumbnail(
            self.landscape, "100x100", cropbox="50,0,150,100"
        )
        engine = PILEngine()
        im = engine.get_image(th)

        self.assertEqual(mean_pixel(0, 50), 255)
        self.assertEqual(mean_pixel(45, 50), 255)
        self.assertEqual(250 < mean_pixel(49, 50) <= 255, True)
        self.assertEqual(mean_pixel(55, 50), 0)
        self.assertEqual(mean_pixel(99, 50), 0)

        # Left
        th = self.BACKEND.get_thumbnail(
            self.landscape, "100x100", cropbox="0,0,100,100"
        )
        engine = PILEngine()
        im = engine.get_image(th)
        for x in range(0, 99, 10):
            for y in range(0, 99, 10):
                self.assertEqual(250 < mean_pixel(x, y) <= 255, True)

        # Right
        th = self.BACKEND.get_thumbnail(
            self.landscape, "100x100", cropbox="100,0,200,100"
        )
        engine = PILEngine()
        im = engine.get_image(th)
        coords = ((x, y) for y in range(0, 99, 10) for x in range(0, 99, 10))

        for x, y in coords:
            self.assertEqual(0 <= mean_pixel(x, y) < 5, True)


@pytest.mark.django_db
class DummyTestCase(unittest.TestCase):
    def setUp(self):
        self.BACKEND = get_module_class(settings.THUMBNAIL_BACKEND)()

    def tearDown(self):
        super().tearDown()
        settings.THUMBNAIL_ALTERNATIVE_RESOLUTIONS = []

    def test_dummy_tags(self):
        settings.THUMBNAIL_DUMMY = True

        val = render_to_string(
            "thumbnaild1.html",
            {
                "anything": "AINO",
            },
        ).strip()
        self.assertEqual(val, '<img style="margin:auto" width="200" height="100">')
        val = render_to_string(
            "thumbnaild2.html",
            {
                "anything": None,
            },
        ).strip()
        self.assertEqual(
            val,
            '<img src="https://dummyimage.com/300x200" width="300" height="200"><p>NOT</p>',
        )
        val = render_to_string("thumbnaild3.html", {}).strip()
        self.assertEqual(
            val, '<img src="https://dummyimage.com/600x400" width="600" height="400">'
        )

        settings.THUMBNAIL_DUMMY = False

    def test_alternative_resolutions(self):
        settings.THUMBNAIL_DUMMY = True
        settings.THUMBNAIL_ALTERNATIVE_RESOLUTIONS = [1.5, 2]
        val = render_to_string("thumbnaild4.html", {}).strip()
        self.assertEqual(
            val,
            '<img src="https://dummyimage.com/600x400" width="600" '
            'height="400" srcset="https://dummyimage.com/1200x800 2x; '
            'https://dummyimage.com/900x600 1.5x">',
        )


class ImageValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.BACKEND = get_module_class(settings.THUMBNAIL_BACKEND)()

    @pytest.mark.skip("See issue #427")
    def test_truncated_validation(self):
        """
        Test that is_valid_image returns false for a truncated image.
        """
        name = "data/broken.jpeg"
        with open(name, "rb") as broken_jpeg:
            data = broken_jpeg.read()

        engine = PILEngine()

        self.assertFalse(engine.is_valid_image(data))

    @pytest.mark.skip("See issue #427. This seems to not-fail with wand")
    def test_truncated_generation_failure(self):
        """
        Confirm that generating a thumbnail for our "broken" image fails.
        """
        name = "data/broken.jpeg"
        with open(name, "rb") as broken_jpeg:

            with self.assertRaises(
                (
                    OSError,
                    IOError,
                )
            ):
                im = default.engine.get_image(broken_jpeg)

                options = ThumbnailBackend.default_options
                ratio = default.engine.get_image_ratio(im, options)
                geometry = parse_geometry("120x120", ratio)
                default.engine.create(im, geometry, options)
