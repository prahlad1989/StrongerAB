import codecs
import csv
import io

import email_validator
import itertools
import json
import logging
from datetime import datetime, timedelta, date, timezone

from django.contrib.auth import login, logout as log_out
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Count
from django.forms import forms, model_to_dict
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, StreamingHttpResponse, HttpResponseNotAllowed
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from Influencers.forms import LoginForm, InfluencerForm
from Influencers.models import Influencer as InfluencerModel, Constants as Constants


from StrongerAB1.settings import LEADSPAN, ADMINSPAN, response_choices, influencer_post_status, paid_unpaid_choices, \
    is_influencer_choices, is_answered_choices
from StrongerAB1.settings import portals as portal_choices
from StrongerAB1.settings import adminMsg
from StrongerAB1.settings import b2b_mandatory_fields
import re

logger = logging.getLogger(__name__)


class Index(TemplateView):
    template_name = 'index.html'


class Login(TemplateView):
    template_name = 'user_login.html'

    def get(self, request, *args, **kwargs):
        context = dict()
        context['form'] = LoginForm()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        loginform = LoginForm(request.POST)
        if loginform.is_valid():
            user = loginform.user
            logger.info('user is %s', user)
            login(request, user)
        return HttpResponseRedirect('all_influencers')


def logout(request):
    log_out(request)
    return HttpResponseRedirect('login')



#creating super class



class BaseView(View):
    model = InfluencerModel

    duplicateCheckField = 'channel_username'

    def getForm(self, request):
        return InfluencerForm(request.POST)

    def delete(self, request, *args, **kwargs):
        item = json.loads(request.body)
        id = item['id']
        item = self.model.objects.get(pk=id)
        if item.created_by_id != request.user.pk and not request.user.is_staff:
            return JsonResponse({'error': "You can't modify Others' Influencers" + adminMsg}, status=500)
        if datetime.now(timezone.utc) - item.created_at > timedelta(
                1) and not request.user.is_staff:
            return JsonResponse({'error': "You can't modify a Lead older than 1 day" + adminMsg}, status=500)

        influ_email = item.email
        item.delete()
        logger.info(
            'Record with email {0} has been deleted by user {1}'.format(influ_email, request.user.get_username()))
        return JsonResponse('ecord with email {0} has been deleted.'.format(influ_email), safe=False, status=200)

    def post(self, request, *args, **kwargs):
        form = self.getForm(request)
        #logger.info("form is {0}".format(form))
        #logger.info("form errors {0}".format(form.errors))
        object = form.save(commit=False)
        object.created_by = request.user
        object.updated_by = request.user
        object.save()
        logger.info(
            "Row with username {0} saved by user {1}".format(object.channel_username, request.user.get_username()))
        return HttpResponse(status=201, content=object)


    def put(self, request, *args, **kwargs):
        item = json.loads(request.body)
        id = item['id']
        index = item['index']
        itemFromDB = self.model.objects.get(pk=id)
        if itemFromDB.created_by_id != request.user.pk and not request.user.is_staff:
            return JsonResponse({'error': "You can't modify Others' Influencers" + adminMsg}, status=500)
        if datetime.now(timezone.utc) - itemFromDB.created_at > timedelta(
                1) and not request.user.is_staff:
            return JsonResponse({'error': "You can't modify a Lead older than 1 day" + adminMsg}, status=500)

        for field in itemFromDB._meta.fields:

            if field.name in item and "_on" in field.name:
                date = datetime.fromtimestamp(item[field.name]).date()
                itemFromDB.__setattr__(field.name, date)

            elif field.name in item and not field.name in ['created_by','updated_by','influencerbase_ptr']:
                #print(field.name)
                itemFromDB.__setattr__(field.name, item[field.name])
        itemFromDB.update_by = request.user
        itemFromDB.save()
        logger.info(
            "Record with influencer name {1} updated by user {0}".format(request.user.get_username(),
                                                                    itemFromDB.channel_username))
        itemFromDB = leadToDict(itemFromDB)
        itemFromDB['index'] = index
        return JsonResponse(itemFromDB, safe=False, status=200)





class InfluencerView(BaseView):
    pass





@login_required()
def index(request):
    context = dict()
    context['portal_choices'] = json.dumps(list(map(lambda x: x[0], portal_choices)))
    countries = Constants.objects.filter(Q(key='countries')).values('value')[0]['value']
    context['countries'] = countries
    collections = Constants.objects.filter(Q(key='collections')).values('value')[0]['value']
    context['collections'] = collections
    channels = Constants.objects.filter(Q(key='chaneels')).values('value')[0]['value']
    context['channels'] = channels
    context["is_user_staff"] = request.user.is_staff
    context["username"] = request.user.get_username()
    influencerFields = InfluencerModel._meta.get_fields()
    influencerFieldsDict = dict()
    for field in influencerFields:
        influencerFieldsDict[field.attname] = field.verbose_name
        influencerFieldsDict[field.verbose_name] = field.attname
    context["influencerFieldsDict"] = influencerFieldsDict
    return render(request,'Influencer.html', context)

@login_required()
def allInfluencers(request):
    context = dict()
    context['portal_choices'] = json.dumps(list(map(lambda x: x[0], portal_choices)))
    countries = Constants.objects.filter(Q(key='countries')).values('value')[0]['value']
    context['list_of_countries'] = countries
    collections = Constants.objects.filter(Q(key='collections')).values('value')[0]['value']
    context['collections'] = collections
    channels = Constants.objects.filter(Q(key='channels')).values('value')[0]['value']
    context['channels'] = channels
    context["is_user_staff"] = request.user.is_staff
    context["username"] = request.user.get_username()
    influencerFields = InfluencerModel._meta.get_fields()
    influencerFieldsDict = dict()
    for field in influencerFields:
        influencerFieldsDict[field.attname] = field.verbose_name
        influencerFieldsDict[field.verbose_name] = field.attname
    context["influencerFieldsDict"] = influencerFieldsDict
    context["influencer_post_status"] = influencer_post_status
    context["paid_unpaid_choices"] = paid_unpaid_choices
    context["is_influencer_choices"] = is_influencer_choices
    context["is_answered_choices"] = is_answered_choices
    return render(request, 'Influencer.html', context)


# helper class; not related to view directly
class Echo:
    def write(self, value):
        return value

#
# class LeadSummary(View):
#     @method_decorator(login_required)
#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)
#
#     model = LeadTable
#
#     def dictToArray(self, lead):
#         arr = []
#         for key, value in lead.items():
#             arr.append(value)
#         return arr
#
#     def getPermittedStartDate(self,request, startDate):
#         if not request.user.is_superuser and request.user.is_staff:
#             allowedStartDate = datetime.today() - timedelta(LEADSPAN)
#             if startDate < allowedStartDate:
#                 return allowedStartDate
#         return startDate
#
#
#     def getFilteredRows(self, request):
#         searchParams = request.GET
#         logger.info("request params for downloading all company summary", searchParams)
#         if not request.user.is_staff:
#             return HttpResponseNotAllowed('method not allowed')
#         startDate = searchParams['startDate']
#         endDate = searchParams['endDate']
#         if startDate is None:
#             raise forms.ValidationError("start date required")
#         elif endDate is None:
#             raise forms.ValidationError("end date required")
#         startDate = datetime.fromtimestamp(int(startDate))
#         startDate = self.getPermittedStartDate(request, startDate)
#         endDate = datetime.fromtimestamp(int(endDate)) + timedelta(1)
#         option = searchParams['option']
#         filterOptions = dict()
#         if option and len(option) > 0:
#             filterOptions[option] = True
#         leads = self.model.objects.select_related('created_by').filter(
#             Q(created_at__gte=startDate) & Q(created_at__lte=endDate) | Q(is_client=True) | Q(is_dnd=True)
#             , **filterOptions)
#         return leads
#
#     # Downloading All compnaies into excel
#     def get(self, request, *args, **kwargs):
#         leads = self.getFilteredRows(request)
#         leads = leads.values('id', LeadTable.company_name.field_name,
#                              LeadTable.position.field_name,
#                              LeadTable.location.field_name,
#                              LeadTable.portals.field_name,
#                              LeadTable.span.field_name,
#                              LeadTable.is_dnd.field_name,
#                              LeadTable.is_client.field_name,
#                              LeadTable.comments.field_name,
#                              LeadTable.response.field_name,
#                              LeadTable.created_at.field_name,
#                              LeadTable.updated_at.field_name,
#                              'created_by',
#                              'created_on',
#                              'created_by__username')
#         output = map(lambda lead: [lead[LeadTable.company_name.field_name], lead[LeadTable.position.field_name],
#                                    lead[LeadTable.location.field_name], lead[LeadTable.portals.field_name], (
#                                                datetime.now().replace(tzinfo=None) - lead[
#                                            LeadTable.created_at.field_name].replace(tzinfo=None)).days,
#                                    lead[LeadTable.span.field_name], lead[LeadTable.is_dnd.field_name],
#                                    lead[LeadTable.is_client.field_name], lead[LeadTable.comments.field_name],
#                                    lead['response'], lead[LeadTable.created_on.field_name],
#                                    lead['created_by__username']], leads)
#         dummyBuffer = Echo()
#         csv_writer = csv.writer(dummyBuffer)
#         csvHeader = ['Company Name', 'Position', 'Location', 'Portals', 'LeadAge', 'Span', 'Is DND', 'Is Client',
#                      LeadTable.comments.field_name, 'Response', LeadTable.created_on.field_name, 'Analyst']
#         output = itertools.chain([csvHeader], output)
#         response = StreamingHttpResponse((csv_writer.writerow(row) for row in output), content_type="text/csv")
#         response['Content-Disposition'] = 'attachment; filename="AllCompanies.csv"'
#         return response
#
#     def getSearchParams(self, request):
#         searchParams = json.loads(request.body)
#         startDate = searchParams['startDate']
#         endDate = searchParams['endDate']
#         if startDate is None:
#             raise forms.ValidationError("start date required")
#         elif endDate is None:
#             raise forms.ValidationError("end date required")
#         startDate = datetime.fromtimestamp(startDate)
#         endDate = datetime.fromtimestamp(endDate) + timedelta(1)
#         return (startDate, endDate)
#
#     # Sending params etc through post, for viewing summary
#     def post(self, request, *args, **kwargs):
#         (startDate, endDate) = self.getSearchParams(request)
#         summary = User.objects.filter(Q(lead__created_at__gte=startDate) & Q(
#             lead__created_at__lte=endDate)).annotate(num_leads=Count('lead')).values('username', 'num_leads')
#         totalLeads = sum((map((lambda x: x['num_leads']), summary)))
#         return JsonResponse({"summary": list(summary), "total": totalLeads}, safe=False, status=200)
#
#
# class B2BLeadSummary(LeadSummary):
#     model = B2BLeadModel
#
#     # Sending params etc through post, for viewing summary
#     def post(self, request, *args, **kwargs):
#         (startDate, endDate) = self.getSearchParams(request)
#         summary = User.objects.filter(Q(b2blead__created_at__gte=startDate) & Q(
#             b2blead__created_at__lte=endDate)).annotate(num_leads=Count('b2blead')).values('username', 'num_leads')
#         totalLeads = sum((map((lambda x: x['num_leads']), summary)))
#         return JsonResponse({"summary": list(summary), "total": totalLeads}, safe=False, status=200)
#
#     def get(self, request, *args, **kwargs):
#         leads = self.getFilteredRows(request)
#         leads = leads.values('id',
#                              B2BLeadModel.company_name.field_name,
#                              B2BLeadModel.full_name.field_name,
#                              B2BLeadModel.first_name.field_name,
#                              B2BLeadModel.last_name.field_name,
#                              B2BLeadModel.designation.field_name,
#                              B2BLeadModel.email.field_name,
#                              B2BLeadModel.linkedin_id.field_name,
#                              B2BLeadModel.position.field_name,
#                              B2BLeadModel.job_location.field_name,
#                              B2BLeadModel.job_posting_links.field_name,
#                              B2BLeadModel.phone_number.field_name,
#                              B2BLeadModel.address.field_name,
#                              B2BLeadModel.state.field_name,
#                              B2BLeadModel.zip_code.field_name,
#                              B2BLeadModel.company_website.field_name,
#                              B2BLeadModel.company_linkedin.field_name,
#                              B2BLeadModel.is_client.field_name,
#                              B2BLeadModel.is_dnd.field_name,
#                              B2BLeadModel.span.field_name,
#                              B2BLeadModel.comments.field_name,
#                              B2BLeadModel.response.field_name,
#                              B2BLeadModel.created_on.field_name,
#                              'created_by__username'
#
#                              )
#
#         output = map(self.dictToArray, leads)
#         dummyBuffer = Echo()
#         csv_writer = csv.writer(dummyBuffer)
#         csvHeader = ['ID', 'Company Name', 'Full Name', 'First Name', 'Last Name', 'Designation', 'Email',
#                      'Linkedin ID', 'Position', 'Job Location', 'Job Posting Links', 'Phone Number', 'Address',
#                      'State/Region', 'Zip Code', 'Company Website', 'Company Linkedin', 'Is DND', 'Is Client', 'Span',
#                      LeadTable.comments.field_name, 'Response', LeadTable.created_on.field_name, 'Analyst']
#         output = itertools.chain([csvHeader], output)
#         response = StreamingHttpResponse((csv_writer.writerow(row) for row in output), content_type="text/csv")
#         response['Content-Disposition'] = 'attachment; filename="B2BLeads.csv"'
#         return response


def getUserNames(request):
    usernames = User.objects.order_by('username').values('username')
    return JsonResponse({"usernames": list(usernames)}, safe=False, status=200)


# it just gives the days between today and respective 'LeadSpan' specified by the amdin
def getLeadsPeriod(user):
    since = datetime.now() - timedelta(LEADSPAN)
    if user.is_staff:
        since = datetime.now() - timedelta(ADMINSPAN)
    return since


def dump(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))


def leadToDict(x):
    item = model_to_dict(x, fields=[field.name for field in x._meta.fields])
    item['created_at'] = x.created_at
    item['updated_at'] = x.updated_at
    item['created_by__username'] = x.created_by.username
    item['updated_by__username'] = x.updated_by.username
    return item


# class LeadsQuery(View):
#
#     @method_decorator(login_required)
#     def dispatch(self, *args, **kwargs):
#         return super().dispatch(*args, **kwargs)
#
#     model = LeadTable
#     # leads search
#     fields_in_response = ('id',
#                           LeadTable.company_name.field_name,
#                           LeadTable.position.field_name,
#                           LeadTable.location.field_name,
#                           LeadTable.portals.field_name,
#                           LeadTable.span.field_name,
#                           LeadTable.is_dnd.field_name,
#                           LeadTable.is_client.field_name,
#                           LeadTable.comments.field_name,
#                           'response',
#                           LeadTable.created_at.field_name,
#                           LeadTable.updated_at.field_name,
#                           'created_by',
#                           'created_on',
#                           'created_by__username')
#
#     def getQueryParams(self, request):
#         searchParams = dict()
#         for k, v in json.loads(request.body).items():
#             if isinstance(v, bool) and v:
#                 searchParams[k] = v
#             elif isinstance(v, str) and len(v) > 0:
#                 if k in ['sortOrder', 'sortField']:
#                     searchParams[k] = v
#                 elif k == 'created_by':
#                     k = "created_by__username"
#                     # searchParams["created_by__username__icontains"] = v
#                 else:
#                     searchParams[k + "__icontains"] = v
#             elif k == 'created_at' and v:
#                 searchParams['created_at__gte'] = datetime.fromtimestamp(v)
#                 searchParams['created_at__lte'] = datetime.fromtimestamp(v) + timedelta(1)
#             elif k in ['pageIndex', 'pageSize']:
#                 searchParams[k] = v
#         pageIndex = searchParams.pop("pageIndex")
#         pageSize = searchParams.pop("pageSize")
#
#         offSet = (pageIndex - 1) * pageSize
#         limitEnds = pageIndex * pageSize
#         return (offSet, limitEnds, searchParams)
#
#     def post(self, request, *args, **kwargs):
#         since = getLeadsPeriod(request.user)
#         offSet, limitEnds, searchParams = self.getQueryParams(request)
#         sortField = None
#         if "sortField" in searchParams:
#             sortField = searchParams.pop("sortField")
#             sortOrder = searchParams.pop("sortOrder")
#             if sortOrder == "desc":
#                 sortField = "-" + sortField
#
#         leadsQuery = self.model.objects.select_related('created_by').filter(
#             Q(created_at__gte=since) | Q(is_client=True) | Q(is_dnd=True),
#             **searchParams)
#         if sortField:
#             leadsQuery = leadsQuery.order_by(sortField)
#         count = leadsQuery.count()
#         leads = leadsQuery.values(*self.fields_in_response)[offSet:limitEnds]
#         leadsJSON = {"data": list(leads), "itemsCount": count}
#         return JsonResponse(leadsJSON, safe=False, status=200)
#


#Influencer query



class InfluencersQuery(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    model = InfluencerModel

    def getDateFields(self):
        return []
        # fields = self.model._meta.get_fields()
        # for field in fields:

    # leads search
    fields_in_response = ('id',
                          InfluencerModel.is_influencer.field_name,
                          'created_by__username',
                          'created_by__id',
                          InfluencerModel.email.field_name,
                          InfluencerModel.is_answered.field_name,
                          InfluencerModel.last_contacted_on.field_name,
                          InfluencerModel.is_duplicate.field_name,
                          InfluencerModel.order_num.field_name,
                          InfluencerModel.order_code.field_name,
                          InfluencerModel.date_of_promotion_on.field_name,
                          InfluencerModel.influencer_name.field_name,
                          InfluencerModel.channel_username.field_name,
                          InfluencerModel.followers_count.field_name,
                          InfluencerModel.country.field_name,
                          InfluencerModel.collection.field_name,
                          InfluencerModel.channel.field_name,
                          InfluencerModel.discount_coupon.field_name,
                          InfluencerModel.valid_from.field_name,
                          InfluencerModel.valid_till.field_name,
                          InfluencerModel.status.field_name,
                          InfluencerModel.status.field_name,
                          InfluencerModel.commission.field_name,
                          InfluencerModel.product_cost.field_name,
                          InfluencerModel.revenue_analysis.field_name,
                          InfluencerModel.revenue_click.field_name,
                          InfluencerModel.comments.field_name,
                          InfluencerModel.created_at.field_name,
                          InfluencerModel.updated_at.field_name,
                          "updated_by__username", "updated_by__id")

    def getQueryParams(self, request):
        searchParams = dict()
        requestBody = json.loads(request.body)
        for k, v in requestBody.items():
            if isinstance(v, bool) and v:
                searchParams[k] = v
            elif isinstance(v, str) and len(v) > 0:
                if k in ['sortOrder', 'sortField']:
                    searchParams[k] = v
                elif k == 'created_by':
                    k = "created_by__username"
                elif k == 'updated_by':
                    k = "updated_by__username"
                    # searchParams["created_by__username__icontains"] = v
                else:
                    searchParams[k + "__icontains"] = v
            elif k == 'created_at' and v:
                searchParams['created_at__gte'] = datetime.fromtimestamp(v)
                searchParams['created_at__lte'] = datetime.fromtimestamp(v) + timedelta(1)
            elif k in ['pageIndex', 'pageSize']:
                searchParams[k] = v
            elif "_on" in k and v:
                searchParams[k+"__gte"] = datetime.fromtimestamp(v).date()
                searchParams[k + "__lte"] = datetime.fromtimestamp(v).date() + timedelta(1)
            elif "__username" not in k and self.model._meta.get_field(k).get_internal_type() == "DateTimeField" and v:
                searchParams[k+"__gte"] = datetime.fromtimestamp(v)
                searchParams[k + "__lte"] = datetime.fromtimestamp(v) + timedelta(1)

        pageIndex = searchParams.pop("pageIndex")
        pageSize = searchParams.pop("pageSize")

        offSet = (pageIndex - 1) * pageSize
        limitEnds = pageIndex * pageSize
        return (offSet, limitEnds, searchParams)

    def post(self, request, *args, **kwargs):
        since = getLeadsPeriod(request.user)
        offSet, limitEnds, searchParams = self.getQueryParams(request)
        sortField = None
        if "sortField" in searchParams:
            sortField = searchParams.pop("sortField")
            sortOrder = searchParams.pop("sortOrder")
            if sortOrder == "desc":
                sortField = "-" + sortField

        query = self.model.objects.select_related('created_by').filter(
            **searchParams)
        if sortField:
            query = query.order_by(sortField)
        count = query.count()
        records = query.values(*self.fields_in_response)[offSet:limitEnds]
        recordsJSON = {"data": list(records), "itemsCount": count}
        return JsonResponse(recordsJSON, safe=False, status=200)




# class B2BLead(Lead):
#     def getModel(self):
#         return B2BLeadModel
#
#     model = B2BLeadModel
#     duplicateCheckField = 'email'
#
#     def getForm(self, request):
#         return B2BLeadForm(request.POST)
#     #
#     # def put(self, request, *args, **kwargs):
#     #     lead = json.loads(request.body)
#     #     id = lead['id']
#     #     leadFromDB = self.getModel().objects.get(pk=id)
#     #     if leadFromDB.created_by_id != request.user.pk and not request.user.is_staff:
#     #         return JsonResponse({'error': "You can't modify Others' Influencers" + adminMsg}, status=500)
#     #     if datetime.now(timezone.utc) - leadFromDB.created_at > timedelta(
#     #             1) and not request.user.is_staff:
#     #         return JsonResponse({'error': "You can't modify a Lead older than 1 day" + adminMsg}, status=500)
#     #
#     #     for field in leadFromDB._meta.fields:
#     #         if field.name in lead and not field.name in ['created_by']:
#     #             leadFromDB.__setattr__(field.name, lead[field.name])
#     #     leadFromDB.save()
#     #     logger.info(
#     #         "lead with company name {1} updated by user {0}".format(request.user.get_username(),
#     #                                                                 leadFromDB.company_name))
#     #     return JsonResponse(leadToDict(leadFromDB), safe=False, status=200)
#
#
# class B2BLeadsQuery(LeadsQuery):
#     @method_decorator(login_required)
#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)
#
#     model = B2BLeadModel
#
#     fields_in_response = ('id', B2BLeadModel.company_name.field_name,
#                           B2BLeadModel.full_name.field_name,
#                           B2BLeadModel.first_name.field_name,
#                           B2BLeadModel.last_name.field_name,
#                           B2BLeadModel.designation.field_name,
#                           B2BLeadModel.email.field_name,
#                           B2BLeadModel.linkedin_id.field_name,
#                           B2BLeadModel.position.field_name,
#                           B2BLeadModel.job_location.field_name,
#                           B2BLeadModel.job_posting_links.field_name,
#                           B2BLeadModel.phone_number.field_name,
#                           B2BLeadModel.address.field_name,
#                           B2BLeadModel.state.field_name,
#                           B2BLeadModel.zip_code.field_name,
#                           B2BLeadModel.company_website.field_name,
#                           B2BLeadModel.company_linkedin.field_name,
#                           B2BLeadModel.is_client.field_name,
#                           B2BLeadModel.is_dnd.field_name,
#                           B2BLeadModel.span.field_name,
#                           B2BLeadModel.comments.field_name,
#                           B2BLeadModel.response.field_name,
#                           'created_by__username',
#                           B2BLeadModel.created_at.field_name,
#                           B2BLeadModel.created_on.field_name)
#
#
# class B2BLeads(B2BLeadsQuery):
#     @method_decorator(login_required)
#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)
#
#     @method_decorator(login_required)
#     def post(self, request, *args, **kwargs):
#         rows = []
#         filterDuplicates = False
#         fields = self.model._meta.get_fields()
#         if request.FILES:
#             csv_file = request.FILES['myfile']
#             rows = list(csv.DictReader(io.StringIO(csv_file.read().decode('ISO-8859-1'))))
#         else:
#             rows = json.loads(request.body)
#
#         # Validation for non emopty
#         mandatoryFields = b2b_mandatory_fields
#         index = 0
#         messages = []
#         for row in rows:
#
#             index += 1
#             for key, value in row.items():
#                 if key in mandatoryFields and not value.strip():
#                     messages.append(key + " is mandatory at row: {0};\n".format(index))
#                 if key == 'Email':
#                     try:
#                         email_validator.validate_email(value)
#                     except email_validator.EmailNotValidError as err:
#                         messages.append(key + "  "+value+" is not valid at row: {0};\n".format(index))
#         if len(messages) > 0:
#             try:
#                 raise ValidationError(messages)
#             except ValidationError as  err:
#                 return JsonResponse({"error": err.messages}, status=500)
#
#         emailsInRows = map(lambda x: x['Email'], rows)
#         if 'filterDuplicates' in request.GET and request.GET['filterDuplicates'] == 'true':
#             filterDuplicates = True
#         span = LeadSpan.objects.get(pk=1)
#         span = span.spanInDays
#         since = datetime.now() - timedelta(span)
#         leadsInTheSpan = self.model.objects.filter(Q(created_at__gte=since) & Q(email__in=emailsInRows)).values(
#             *self.fields_in_response)
#         duplicates = []
#         createdLeadsCount = 0
#         statusJSON = dict()
#         with transaction.atomic():
#             fields = self.model._meta.get_fields()
#             oldLeadsToBeDeleted = []
#             for row in reversed(rows):
#                 matchedDBLead = None
#                 emailExists = False
#                 for lead in leadsInTheSpan:
#                     if not filterDuplicates and row['Email'] == lead['email']:
#                         row["old_id"] = lead["id"]
#                         duplicates.append([row, lead])
#                         emailExists = True
#                         # logger.info('duplicate email %s and rowid is %d', row['Email'],lead['id'])
#                         break
#
#                 if not emailExists:
#                     # assume request coming from UI after user selects skip/override
#                     if "old_id" in row:
#                         # logger.info("old_id", str(row["old_id"]))
#                         oldLeadsToBeDeleted.append(row["old_id"])
#                     b2b_lead = self.model()
#                     for field in fields:
#                         if field.verbose_name in row:
#                             b2b_lead.__setattr__(field.attname, row[field.verbose_name])
#                     b2b_lead.created_by = request.user
#                     b2b_lead.save()
#                     createdLeadsCount += 1
#             self.model.objects.filter(Q(id__in=oldLeadsToBeDeleted)).delete()
#         duplicates.reverse()
#         statusJSON['duplicates'] = duplicates
#         statusJSON['createdCount'] = createdLeadsCount
#         return JsonResponse(statusJSON, safe=False, status=201)
#
