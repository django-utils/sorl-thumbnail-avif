from sorl.thumbnail.base import ThumbnailBackend
from sorl.thumbnail.conf import settings
from sorl.thumbnail.conf import defaults as default_settings
from sorl.thumbnail.helpers import serialize, tokey


EXTENSIONS = {
    "JPEG": "jpg",
    "PNG": "png",
    "GIF": "gif",
    "WEBP": "webp",
    "AVIF": "avif",
}


class AvifThumbnail(ThumbnailBackend):
    def _get_format(self, source):
        file_extension = self.file_extension(source)

        if file_extension == ".avif":
            return "AVIF"
        elif file_extension == ".jpg" or file_extension == ".jpeg":
            return "JPEG"
        elif file_extension == ".png":
            return "PNG"
        elif file_extension == ".gif":
            return "GIF"
        elif file_extension == ".webp":
            return "WEBP"
        else:
            from django.conf import settings

            return getattr(
                settings, "THUMBNAIL_FORMAT", default_settings.THUMBNAIL_FORMAT
            )

    def _get_thumbnail_filename(self, source, geometry_string, options):
        key = tokey(source.key, geometry_string, serialize(options))
        path = f"{key[:2]}{key[2:4]}{key}"
        return f"{settings.THUMBNAIL_PREFIX}{path}.{EXTENSIONS[options['format']]}"
