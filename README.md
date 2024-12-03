# sorl thumbnail avif

a python package to add avif support to sorl-thumbnail.

**note**: this package will get support until sorl-thumbnail supports avif, then it'll be archived.

**nota2**: this package uses pillow.

### Installation

``` bash
    pip install sorl-thumbnail-avif
```

### Usage:

add these lines to your settings file:

``` python
    THUMBNAIL_FORMAT = "AVIF"
    THUMBNAIL_ENGINE = "sorl_thumbnail_avif.thubmnail.engines.AvifEngine"
    THUMBNAIL_BACKEND = "sorl_thumbnail_avif.thubmnail.AvifThumbnail"
```

**note**: you can use any of the sorl-thumbnail supported formats as well, so `JPEG` or others also work.
