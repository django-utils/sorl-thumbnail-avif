import os

import pytest

from sorl.thumbnail import get_thumbnail
from sorl.thumbnail.conf import settings
from sorl.thumbnail.engines.pil_engine import Engine as PILEngine
from sorl.thumbnail.images import ImageFile

from .utils import BaseStorageTestCase


class AlternativeResolutionsTest(BaseStorageTestCase):
    name = "retina.jpg"

    def setUp(self):
        settings.THUMBNAIL_ALTERNATIVE_RESOLUTIONS = [1.5, 2]
        super().setUp()
        self.maxDiff = None

    def tearDown(self):
        super().tearDown()
        settings.THUMBNAIL_ALTERNATIVE_RESOLUTIONS = []

    @pytest.mark.django_db
    def test_retina(self):
        get_thumbnail(self.image, "50x50")

        actions = [
            "exists: test/cache/007300730ba780321843a3a7584ab165750c.avif",
            # save regular resolution, same as in StorageTestCase
            "open: retina.jpg",
            "save: test/cache/007300730ba780321843a3a7584ab165750c.avif",
            "get_available_name: test/cache/007300730ba780321843a3a7584ab165750c.avif",
            "exists: test/cache/007300730ba780321843a3a7584ab165750c.avif",
            # save the 1.5x resolution version
            "save: test/cache/007300730ba780321843a3a7584ab165750c@1.5x.avif",
            "get_available_name: test/cache/007300730ba780321843a3a7584ab165750c@1.5x.avif",
            "exists: test/cache/007300730ba780321843a3a7584ab165750c@1.5x.avif",
            # save the 2x resolution version
            "save: test/cache/007300730ba780321843a3a7584ab165750c@2x.avif",
            "get_available_name: test/cache/007300730ba780321843a3a7584ab165750c@2x.avif",
            "exists: test/cache/007300730ba780321843a3a7584ab165750c@2x.avif",
        ]
        self.assertEqual(self.log, actions)

        path = os.path.join(
            settings.MEDIA_ROOT,
            "test/cache/007300730ba780321843a3a7584ab165750c@1.5x.avif",
        )

        with open(path) as fp:
            engine = PILEngine()
            self.assertEqual(
                engine.get_image_size(engine.get_image(ImageFile(file_=fp))), (75, 75)
            )
