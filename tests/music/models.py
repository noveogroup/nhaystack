# coding: utf-8

from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Musician(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    instrument = models.CharField(max_length=100)

    def __str__(self):
        return '{} {} ({})'.format(self.first_name, self.last_name, self.instrument)


@python_2_unicode_compatible
class Album(models.Model):
    artist = models.ForeignKey(Musician, related_name='albums', on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    release_date = models.DateField()
    num_stars = models.IntegerField()

    def __str__(self):
        return '{} ({})'.format(self.name, self.release_date)
