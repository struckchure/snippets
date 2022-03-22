from django.db import models
from django.template.defaultfilters import slugify
from rest_framework.generics import GenericAPIView, get_object_or_404
import uuid, re


class BaseModel(models.Model):

    id = models.SlugField(primary_key=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def unique_slugify(
        self, value, slug_field_name="slug", queryset=None, slug_separator="-"
    ):
        """
        Calculates and stores a unique slug of ``value`` for an instance.

        ``slug_field_name`` should be a string matching the name of the field to
        store the slug in (and the field to check against for uniqueness).

        ``queryset`` usually doesn't need to be explicitly provided - it'll default
        to using the ``.all()`` queryset from the model's default manager.
        """
        instance = self
        slug_field = instance._meta.get_field(slug_field_name)

        slug = getattr(instance, slug_field.attname)
        slug_len = slug_field.max_length

        # Sort out the initial slug, limiting its length if necessary.
        slug = slugify(value)
        if slug_len:
            slug = slug[:slug_len]
        slug = self._slug_strip(slug, slug_separator)
        original_slug = slug

        # Create the queryset if one wasn't explicitly provided and exclude the
        # current instance from the queryset.
        if queryset is None:
            queryset = instance.__class__._default_manager.all()
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)

        # Find a unique slug. If one matches, at '-2' to the end and try again
        # (then '-3', etc).
        next = 2
        while not slug or queryset.filter(**{slug_field_name: slug}):
            slug = original_slug
            end = "%s%s" % (slug_separator, next)
            if slug_len and len(slug) + len(end) > slug_len:
                slug = slug[: slug_len - len(end)]
                slug = self._slug_strip(slug, slug_separator)
            slug = "%s%s" % (slug, end)
            next += 1

        setattr(instance, slug_field.attname, slug)

    def _slug_strip(self, value, separator="-"):
        """
        Cleans up a slug by removing slug separator characters that occur at the
        beginning or end of a slug.

        If an alternate separator is used, it will also replace any instances of
        the default '-' separator with the new separator.
        """
        separator = separator or ""
        if separator == "-" or not separator:
            re_sep = "-"
        else:
            re_sep = "(?:-|%s)" % re.escape(separator)
        # Remove multiple instances and if an alternate separator is provided,
        # replace the default '-' separator.
        if separator != re_sep:
            value = re.sub("%s+" % re_sep, separator, value)
        # Remove separator from the beginning and end of the slug.
        if separator:
            if separator != "-":
                re_sep = re.escape(separator)
            value = re.sub(r"^%s+|%s+$" % (re_sep, re_sep), "", value)
        return value


class View(GenericAPIView):
    def get_object(self, *args, **kwargs):
        obj = get_object_or_404(*args, **kwargs)
        self.check_object_permissions(self.request, obj)

        return obj
