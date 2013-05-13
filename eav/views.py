import json

from django.views.generic.base import View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from .models import TreeItem

class TreeItemChildren(View):
    """A reusable utility for getting the children of a tree item"""

    def get(self, request, *args, **kwargs):

        parent_id = request.GET.get('parent')
        parent = get_object_or_404(TreeItem, pk=parent_id)

        items = list(parent.children.values_list('id', 'value'))

        return HttpResponse(
            json.dumps(items),
            mimetype='application/json; charset=UTF-8'
        )
