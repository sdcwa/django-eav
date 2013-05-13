#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
#
#    This software is derived from EAV-Django originally written and
#    copyrighted by Andrey Mikhaylenko <http://pypi.python.org/pypi/eav-django>
#
#    This is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This software is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with EAV-Django.  If not, see <http://gnu.org/licenses/>.
'''
#####
forms
#####

The forms used for admin integration

Classes
-------
'''
from copy import deepcopy

from django.forms import BooleanField, CharField, DateTimeField, FloatField, \
                         IntegerField, ModelForm, ModelChoiceField, ValidationError
from django.forms.widgets import MultiWidget, Select
from django.contrib.admin.widgets import AdminSplitDateTime
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from .models import TreeItem


class TreeItemWidget(MultiWidget):

    def __init__(self, querysets, attrs={}):
        self._widgets = []
        for qs in querysets:
            this_attrs = attrs.copy()
            if qs:
                choices = qs.values_list('id', 'value') if qs else ()
            else:
                choices = ()
                #this_attrs.update({'disabled': 'disabled'})

            self._widgets.append(Select(attrs=this_attrs, choices=choices))
        super(TreeItemWidget, self).__init__(self._widgets, attrs)

    def decompress(self, value):
        """
        Take a single stored leaf node value and return additional values for
        each parent tier. If no leaf node value exists, return None values for
        each tier.
        """
        if value:
            ti = TreeItem.objects.get(pk=value)
            ancestors = ti.get_ancestors().exclude(pk=ti.get_root().id)
            return [a.id for a in ancestors] + [ti.id]
        return [None for w in range(len(self._widgets))]

    def render(self, name, value, attrs=None):
        rendered = super(TreeItemWidget, self).render(name, value, attrs)
        treefield_script = """
            <script type="text/javascript">
              $.fn.treefield && $('#id_{0}_{1}').treefield(treeChildUrl);
            </script>
        """
        for i in range(len(self._widgets)-1):
            rendered += mark_safe(treefield_script.format(name, i))
        return rendered

    def format_output(self, rendered_widgets):
        return u''.join(rendered_widgets)

    def value_from_datadict(self, data, files, name):
        values = [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)]
        try:
            return values[-1]
        except ValueError:
            return ''


class BaseDynamicEntityForm(ModelForm):
    '''
    ModelForm for entity with support for EAV attributes. Form fields are
    created on the fly depending on Schema defined for given entity instance.
    If no schema is defined (i.e. the entity instance has not been saved yet),
    only static fields are used. However, on form validation the schema will be
    retrieved and EAV fields dynamically added to the form, so when the
    validation is actually done, all EAV fields are present in it (unless
    Rubric is not defined).
    '''

    FIELD_CLASSES = {
        'text': CharField,
        'float': FloatField,
        'int': IntegerField,
        'date': DateTimeField,
        'bool': BooleanField,
        'enum': ModelChoiceField,
        'tree': ModelChoiceField,
    }

    def __init__(self, data=None, *args, **kwargs):
        super(BaseDynamicEntityForm, self).__init__(data, *args, **kwargs)
        config_cls = self.instance._eav_config_cls
        self.entity = getattr(self.instance, config_cls.eav_attr)
        self._build_dynamic_fields()

    def get_attributes(self):
        return self.entity.get_all_attributes()

    def _build_dynamic_fields(self):
        # reset form fields
        self.fields = deepcopy(self.base_fields)

        for attribute in self.get_attributes():
            value = getattr(self.entity, attribute.slug)

            defaults = {
                'label': attribute.name.capitalize(),
                'required': attribute.required,
                'help_text': attribute.help_text,
                'validators': attribute.get_validators(),
            }

            datatype = attribute.datatype
            if datatype == attribute.TYPE_ENUM:
                defaults.update({
                    'queryset': attribute.get_choices(),
                    'empty_label': '-----',
                })

                if value:
                    defaults.update({'initial': value})

            elif datatype == attribute.TYPE_DATE:
                defaults.update({'widget': AdminSplitDateTime})

            elif datatype == attribute.TYPE_OBJECT:
                continue

            elif datatype == attribute.TYPE_TREE:
                defaults.update({'queryset': attribute.tree_item_parent.get_leafnodes()})
                depth = attribute.tree_item_parent.get_leafnodes()[0].get_level()
                querysets = []

                if value:
                    current_value = value
                    while current_value != attribute.tree_item_parent:
                        # cannot use get_siblings() because we need to include current_value
                        querysets.append(current_value.parent.children.all())
                        current_value = current_value.parent
                    querysets.reverse()
                    assert depth == len(querysets), 'Need querysets for each level'
                else:
                    querysets.append(attribute.tree_item_parent.children.all())
                    for i in range(depth - 1):
                        querysets.append([])

                defaults.update({
                    'widget': TreeItemWidget(querysets),
                    'initial': value,
                })

            MappedField = self.FIELD_CLASSES[datatype]
            self.fields[attribute.slug] = MappedField(**defaults)

            # fill initial data (if attribute was already defined)
            if value and not datatype == attribute.TYPE_ENUM: #enum done above
                self.initial[attribute.slug] = value

    def save(self, commit=True):
        """
        Saves this ``form``'s cleaned_data into model instance
        ``self.instance`` and related EAV attributes.

        Returns ``instance``.
        """

        if self.errors:
            raise ValueError(_(u"The %s could not be saved because the data"
                             u"didn't validate.") % \
                             self.instance._meta.object_name)

        # create entity instance, don't save yet
        instance = super(BaseDynamicEntityForm, self).save(commit=False)

        # assign attributes
        for attribute in self.get_attributes():
            value = self.cleaned_data.get(attribute.slug)
            setattr(self.entity, attribute.slug, value)

        # save entity and its attributes
        if commit:
            instance.save()

        return instance
