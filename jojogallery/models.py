from django.db import models
import django.utils.timezone as timezone
from easy_thumbnails.fields import ThumbnailerImageField
class user(models.Model):
    username=models.CharField(max_length=32)
    password=models.CharField(max_length=32)
    permission=models.DecimalField(max_digits=10,decimal_places=0)
# Create your models here.
class imgApartMent(models.Model):
    caption=models.CharField(max_length=32,default=1)
class imgDetail(models.Model):
    caption=models.CharField(max_length=32)
    apartment=models.ForeignKey('imgApartMent',on_delete=models.CASCADE)
    idate = models.CharField(max_length=64)
    folder=models.CharField(max_length=128,default='')
    author = models.CharField(max_length=32, default='')
    keyword=models.CharField(max_length=128,default='')
class imgUrl(models.Model):
    iurl=ThumbnailerImageField(upload_to='upload/',blank=True)
    iCaption=models.ForeignKey('imgDetail',on_delete=models.CASCADE)
    idate= models.CharField(max_length=64)
    iname=models.CharField(max_length=64)
    iChecked=models.BooleanField(default=False)
    iDevice=models.CharField(max_length=64,default='avatar')
