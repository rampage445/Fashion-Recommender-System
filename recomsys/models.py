from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.
def _upload(instance,filename):
    return f'{instance.gender}/{instance.category}/{filename}'

class Item(models.Model):
    item_no = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    img = models.ImageField(upload_to=_upload)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gender = models.CharField(max_length=10)
    category = models.CharField(max_length=50)
    #related_items = models.ManyToManyField('self', blank=True, symmetrical=True)
    #primary_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_category', verbose_name='Primary Category')
    #related_categories = models.ManyToManyField(Category, blank=True, related_name='related_categories', verbose_name='Related Categories')
    color = models.CharField(max_length=20)
    description = models.TextField()

class Favlist(models.Model):
    user = models.ForeignKey(User,null=True,on_delete=models.SET_NULL)
    item = models.ForeignKey(Item,null=True,on_delete=models.SET_NULL)

class Wishlist(models.Model):
    user = models.ForeignKey(User,null=True,on_delete=models.SET_NULL)
    item = models.ForeignKey(Item,null=True, on_delete=models.SET_NULL)
    
class Recommend(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    search_no = models.IntegerField()
    array = models.JSONField() 

