from django.db import models
from django.db.models.fields import related
from djangotoolbox import fields
from django import forms


__all__ = ('RelListField',)

class ListWidget(forms.TextInput):
    def render(self, name, value, attrs=None):
        if isinstance(value, (list, tuple)):
            value = u', '.join([unicode(v) for v in value])
        return super(ListWidget, self).render(name, value, attrs)

class ListFormField(forms.Field):
    widget = ListWidget
    def clean(self, value):
        return [v.strip() for v in value.split(',') if len(v.strip()) > 0]

class RelListField(fields.AbstractIterableField, related.ManyToOneRel):
    """
    Field representing a Python ``list``.

    If the optional keyword argument `ordering` is given, it must be a callable
    that is passed to :meth:`list.sort` as `key` argument. If `ordering` is
    given, the items in the list will be sorted before sending them to the
    database.
    """
    _type = list

    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            if isinstance(args[0], related.RelatedField) and not isinstance(args[0], models.ForeignKey):
                raise TypeError("%r is not a ForeignKey, but is related." % args[0])
            self.is_related = isinstance(args[0], models.ForeignKey)
        self.ordering = kwargs.pop('ordering', None)
        if self.ordering is not None and not callable(self.ordering):
            raise TypeError("'ordering' has to be a callable or None, "
                            "not of type %r" %  type(self.ordering))
        super(RelListField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        raise Exception(value)

    def contribute_to_class(self, cls, name):
        super(RelListField, self).contribute_to_class(cls, name)
        if not isinstance(self.item_field, models.ForeignKey):
            return
        setattr(cls, self.name, RelListFieldDescriptor(self))

    def _convert(self, func, values, *args, **kwargs):
        values = super(RelListField, self)._convert(func, values, *args, **kwargs)
        if values is not None and self.ordering is not None:
            values.sort(key=self.ordering)
        return values

    def get_attname(self):
        if self.is_related:
            return '%s_data' % self.name
        else:
            return super(RelListField, self).get_attname()

    def set_attname(self, value):
        pass

    def formfield(self, **kwargs):
        defaults = {'form_class': ListFormField}
        defaults.update(kwargs)
        return models.Field.formfield(self, **defaults)

    attname = property(get_attname, set_attname)

class RelListFieldDescriptor(object):
    def __init__(self, field):
        self.field = field
        self.related = field.item_field
        self.cache_name = field.get_cache_name()
        self.is_related = bool(self.related.rel)

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        try:
            return getattr(instance, self.cache_name)
        except AttributeError:
            raw_data = getattr(instance, self.field.attname)
            if not self.is_related:
                return raw_data
            rows = self.related.rel.to.objects.filter(pk__in = raw_data)
            row_dict = dict((row.pk, row) for row in rows)
            row_list = [row_dict[pk] for pk in raw_data if pk in row_dict]
            setattr(instance, self.cache_name, row_list)

    def __set__(self, instance, value):
        value = list(value)
        setattr(instance, self.cache_name, value)
        if not self.is_related:
            setattr(instance, self.field.attname, value)
            return
        
        new_data = [row.pk if isinstance(row, self.related.rel.to) else row
                    for row in value]
        setattr(instance, self.field.attname, new_data)
