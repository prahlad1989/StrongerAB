from django.contrib.auth.models import User
from django.db import models
from StrongerAB1.settings import portals as portal_choices, is_influencer_choices
from StrongerAB1.settings import paid_unpaid_choices,influencer_post_status, is_answered_choices

class InfluencerBase(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, blank=True, null=True, related_name='created_by_user')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, blank=True, null=True, related_name='updated_by_user')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(verbose_name='Updated At',default=None, blank=True, null=True )

    class Meta:
        ordering = ["-created_at", "-updated_at"]
        indexes = [models.Index(fields=[ '-created_at', '-updated_at', 'created_by'])]

class Country(models.Model):
    id = models.IntegerField(unique=True,primary_key=True)
    name=models.CharField(max_length=80)
    code = models.CharField(max_length=10)
    continent = models.CharField(max_length=20)
    isEU =models.BooleanField()

class OrderInfo(models.Model):
    number = models.IntegerField()
    orderDate = models.DateTimeField()
    discount_coupons = models.CharField(max_length=100, null=True)
    grandTotal = models.FloatField(default=0)
    status = models.CharField(choices= map(lambda x:(x,x), is_answered_choices), max_length=10)
    country = models.CharField(max_length=70, null=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

class UserPreferences(InfluencerBase):
    influe_field_preferences = models.TextField(verbose_name='Influencer Field Preferences')


class Influencer(InfluencerBase):
    post_status = map(lambda x: (x, x), influencer_post_status)
    paid_unpaid_choices = map(lambda x: (x, x), paid_unpaid_choices)
    is_influencer_choices = map(lambda x: (x, x), is_influencer_choices)
    is_answered_choices = map(lambda x: (x, x), is_answered_choices)
    is_influencer = models.CharField(max_length=12, verbose_name='Influencer/Prospect', choices=is_influencer_choices, null=False, blank=False)
    email = models.EmailField(null=False, verbose_name='Email', blank=False)
    is_answered = models.CharField( verbose_name='Answered', choices=is_answered_choices, max_length=5, null=True, blank=True)
    last_contacted_on = models.DateField(verbose_name='Last Contacted Date', null=True)
    is_duplicate = models.BooleanField(default=False, verbose_name='Duplicate?')
    order_num = models.CharField(null=True, blank=True, verbose_name='Order Number',max_length=50)
    order_code = models.CharField(null=True, blank=True, verbose_name='Order Code', max_length=50)
    date_of_promotion_on = models.DateField(verbose_name='Day of Promotion', null=True)
    influencer_name = models.CharField(max_length=100, verbose_name='Name', null=False, blank=False)
    paid_or_unpaid = models.CharField(max_length=10, default=None, null=True, choices=paid_unpaid_choices,
                                verbose_name='Paid/Unpaid', blank=True)
    channel_username =  models.CharField( max_length=100, verbose_name='Instagram Username', null=True)
    followers_count =  models.IntegerField(null=True, verbose_name='Followers')
    channel = models.CharField( max_length=200, verbose_name='Channel',  null=True)
    country = models.CharField(null=False, verbose_name='Country',max_length=100)
    collection = models.CharField(null=True, verbose_name='Collection', max_length=100)
    discount_coupon = models.CharField(null=True, verbose_name='Discount Code', max_length=100)
    valid_from = models.DateTimeField(verbose_name='Valid From', null=True)
    valid_till = models.DateTimeField(verbose_name='Valid Till', null=True)
    status = models.CharField(max_length=30, default=None, null=True, verbose_name='Status',choices=post_status)  # need to be correctd
    commission = models.FloatField(max_length=10, verbose_name='Fixed Fee/Commission', null=True, default=0)
    product_cost = models.FloatField( verbose_name='Product Cost', null=True, default=0)
    revenue_analysis = models.FloatField(verbose_name='Revenue Analysis', null=True, default=0)
    revenue_click = models.FloatField( verbose_name='Revenue Qlik', null=True, default=0)
    #roi = models.FloatField(verbose_name='ROI', null=True)
    currency = models.CharField(max_length=20, verbose_name='Currency', null=True)
    comments = models.TextField(default="", blank=True, null=True, verbose_name='Comments', max_length=500)
    is_old_record = models.BooleanField(default=False,null=True, verbose_name='Is Old Record?')
    centra_update_at = models.DateTimeField(verbose_name='Centra Update At', blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=['email','channel_username', '-valid_from'])]

class Constants(InfluencerBase):
    key = models.CharField(max_length=100, verbose_name='key', null=False, blank=False, unique=True)
    value  = models.TextField(verbose_name='value', null=False, blank=False)

