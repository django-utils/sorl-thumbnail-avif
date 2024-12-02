from io import BytesIO
from sorl.thumbnail.engines.pil_engine import Engine

from PIL import Image, ImageFile
from PIL.ImageFilter import GaussianBlur
import pillow_avif  # noqa: F401


class AvifEngine(Engine):
    def get_image(self, source):
        buffer = BytesIO(source.read())
        return Image.open(buffer)

    def is_valid_image(self, raw_data):
        buffer = BytesIO(raw_data)
        try:
            trial_image = Image.open(buffer)
            trial_image.verify()
        except Exception:
            return False
        return True

    def _padding(self, image, geometry, options):
        x_image, y_image = self.get_image_size(image)
        left = int((geometry[0] - x_image) / 2)
        top = int((geometry[1] - y_image) / 2)
        color = options.get("padding_color")
        im = Image.new(image.mode, geometry, color)
        im.paste(image, (left, top))
        return im

    def _get_raw_data(
        self, image, format_, quality, image_info=None, progressive=False
    ):
        # Increase (but never decrease) PIL buffer size
        ImageFile.MAXBLOCK = max(ImageFile.MAXBLOCK, image.size[0] * image.size[1])
        bf = BytesIO()

        params = {
            "format": format_,
            "quality": quality,
            "optimize": 1,
        }

        # keeps icc_profile
        if "icc_profile" in image_info:
            params["icc_profile"] = image_info["icc_profile"]

        raw_data = None

        if format_ == "JPEG" and progressive:
            params["progressive"] = True
        try:
            # Do not save unnecessary exif data for smaller thumbnail size
            params.pop("exif", {})
            image.save(bf, **params)
        except OSError:
            # Try without optimization.
            params.pop("optimize")
            image.save(bf, **params)
        else:
            raw_data = bf.getvalue()
        finally:
            bf.close()

        return raw_data

    def _blur(self, image, radius):
        return image.filter(GaussianBlur(radius=radius))
