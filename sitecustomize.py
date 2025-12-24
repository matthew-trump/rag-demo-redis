# Local shim to keep environs/pymilvus happy with newer marshmallow releases.
# marshmallow 4.x no longer exposes __version_info__ or accepts the "missing"
# kwarg that environs expects. We add the attribute and map missing->load_default.
import marshmallow as _mm  # type: ignore
import marshmallow.fields as _mm_fields  # type: ignore

# Provide __version_info__ if absent
ver = getattr(_mm, "__version__", None)
parts = (0, 0, 0)
if isinstance(ver, str):
    try:
        parts = tuple(int(p) for p in ver.split(".") if p.split(".")[0].isdigit())
    except Exception:
        parts = (0, 0, 0)
if not isinstance(getattr(_mm, "__version_info__", None), tuple):
    _mm.__version_info__ = parts  # type: ignore[attr-defined]
else:
    _mm.__version_info__ = tuple(_mm.__version_info__)  # type: ignore[attr-defined]

# Map missing -> load_default if the signature no longer supports it
_orig_field_init = _mm_fields.Field.__init__
if "missing" not in _orig_field_init.__code__.co_varnames:
    def _patched_field_init(self, *args, **kwargs):  # type: ignore
        if "missing" in kwargs and "load_default" not in kwargs:
            kwargs["load_default"] = kwargs.pop("missing")
        return _orig_field_init(self, *args, **kwargs)
    _mm_fields.Field.__init__ = _patched_field_init  # type: ignore

# Ensure Field has a .missing attribute for callers that check it
if not hasattr(_mm_fields.Field, "missing"):
    _mm_fields.Field.missing = None  # type: ignore[attr-defined]
