from django.contrib.auth.models import User
from django.db import models
from StrongerAB1.settings import portals as portal_choices
from StrongerAB1.settings import response_choices

class B2BLead(models.Model):
    company_name = models.CharField(max_length=100, verbose_name='Company Name', null=False, blank=False)
    full_name = models.CharField(max_length=100, verbose_name='Full Name', null=False, blank=False)
    first_name = models.CharField(max_length=50, verbose_name='First Name', null=True)
    last_name = models.CharField(max_length=50, verbose_name='Last Name', null=True)
    designation = models.CharField(max_length=200, null=False, verbose_name='Designation', blank=False)
    email = models.EmailField(null=False, verbose_name='Email', blank=False)
    linkedin_id = models.CharField(max_length=1000, null=False, verbose_name='Linkedin ID', blank=False)
    position = models.CharField(max_length=200, null=False, verbose_name='Position', blank=False)
    job_location = models.CharField(max_length=200, verbose_name='Job Location', null=False, blank=False)
    job_posting_links = models.TextField(verbose_name='Job Posting Links', null=False, blank=False)
    phone_number = models.TextField(verbose_name='Phone Number', max_length=50)
    address = models.TextField(verbose_name='Address')
    state = models.CharField(verbose_name='State/Region', max_length=50)
    zip_code = models.CharField(verbose_name='Zip Code', max_length=10)
    company_website = models.CharField(verbose_name='Company Website', max_length=2000, null=False)
    company_linkedin = models.CharField(verbose_name='Company Linkedin', max_length=2000, null=False, blank=False)
    is_client = models.BooleanField(default=False, verbose_name='Is Client')
    is_dnd = models.BooleanField(default=False, verbose_name='Is DND')
    span = models.IntegerField(default=20, verbose_name='Span')
    comments = models.TextField(default="", blank=True, null=True, verbose_name='Comments')
    response = models.CharField(max_length=20, default=None, null=True, choices=response_choices,
                                verbose_name='Response')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    created_on = models.DateField(auto_now=True, verbose_name='Created On')
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=['company_name', '-created_at', '-updated_at', 'company_name', '-created_on'])]

class Lead(models.Model):
    company_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, verbose_name='Position')
    location = models.CharField(max_length=200, default=None, null=True, blank=True, verbose_name='Location')
    portals = models.CharField(max_length=100, choices=portal_choices)
    is_client = models.BooleanField(default=False, verbose_name='Is Client')
    span = models.IntegerField(default=20, verbose_name='Span')
    is_dnd = models.BooleanField(default=False, verbose_name='Is DND')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_on = models.DateField(auto_now=True, verbose_name='Created On')
    comments = models.TextField(default="", blank=True, null=True, verbose_name='Comments')
    response = models.CharField(max_length=20, default=None, null=True, choices=response_choices,
                                verbose_name='Response')
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=['company_name', '-created_at', '-updated_at', 'company_name', '-created_on'])]


class LeadSpan(models.Model):
    spanInDays = models.IntegerField(choices=(
    (15, '15'), (20, '20'), (25, '25'), (30, '30'), (35, '35'), (40, '40'), (45, '45'), (50, '50'), (55, '55'),
    (60, '60')), default=30)


class MasterLead(models.Model):
    company_name = models.CharField(max_length=100)
    contact_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    email_id = models.EmailField()
    phone1 = models.CharField(max_length=100)
    phone2 = models.CharField(max_length=100)
    address = models.TextField()
    location = models.TextField()
    company_url = models.TextField()
    job_position = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, blank=True, null=True)
