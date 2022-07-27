# -*- coding: utf-8 -*-

from cedes.core import logger
from cioppino.twothumbs import rate
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import traverse
from zope.annotation import IAnnotations
from zope.interface import implementer
from zope.interface import provider


@provider(ISectionBlueprint)
@implementer(ISection)
class Yays(object):
    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

    def __iter__(self):
        for item in self.previous:
            obj = traverse(self.context, item['_path'], None)

            # path doesn't exist
            if obj is None:
                yield item
                continue

            if '__annotations__' not in item:
                logger.warning("No __annotations__ for %s" % item['_path'])
            else:
                user_ids = item['__annotations__'].get('cioppino.twothumbs.yays', ())
                annotations = IAnnotations(obj)
                if user_ids and not annotations.get('cioppino.twothumbs.yays', ()):
                    rate.setupAnnotations(obj)
                    for user_id in user_ids:
                        rate.loveIt(obj, user_id)

            yield item
