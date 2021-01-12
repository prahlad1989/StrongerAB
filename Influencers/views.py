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
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from Influencers.forms import LoginForm, InfluencerForm
from Influencers.models import Influencer as InfluencerModel, Constants as Constants
from Influencers.tasks import demo_task

from StrongerAB1.settings import LEADSPAN, ADMINSPAN, influencer_post_status, paid_unpaid_choices, \
    is_influencer_choices, is_answered_choices
from StrongerAB1.settings import adminMsg
from StrongerAB1.settings import b2b_mandatory_fields
from StrongerAB1.settings import influencer_mandatory_fields
import re
from .tasks import centraOrdersUpdate
logger = logging.getLogger(__name__)




@csrf_exempt
def tasks(request):
    if request.method == 'GET':
        message = request.GET['query']
        if message:
            demo_task(message)
        return _post_tasks(request)
    else:
        return HttpResponse("Send proper request", status=405)

def _post_tasks(request):
    message = request.POST['message']
    logger.debug('calling demo_task. message={0}'.format(message))
    demo_task(message)
    return JsonResponse({}, status=302)

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

    def _getForm(self, request):
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
        form = self._getForm(request)
        #logger.info("form is {0}".format(form))
        logger.error("form errors {0}".format(form.errors))
        #check if already record exists with email

        object = form.save(commit=False)
        rows = self.model.objects.filter(Q(email__iexact=object.email))
        if rows and len(rows) > 0:
            object.is_duplicate = True
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
            if field.name in item and "_on" in field.name and item[field.name]:
                date = datetime.fromtimestamp(item[field.name]).date()
                itemFromDB.__setattr__(field.name, date)

            elif field.name in item and not field.name in ['created_by','updated_by','influencerbase_ptr']:
                #print(field.name)
                itemFromDB.__setattr__(field.name, item[field.name])
        itemFromDB.updated_by = request.user
        itemFromDB.save()
        logger.info(
            "Record with influencer name {1} updated by user {0}".format(request.user.get_username(),
                                                                    itemFromDB.channel_username))
        itemFromDB = leadToDict(itemFromDB)
        itemFromDB['index'] = index
        return JsonResponse(itemFromDB, safe=False, status=200)


class CentraUpdate(object):
    def update(self):
        pass

class OrdersUpdate(CentraUpdate):
    def update(self):
        pass

class ValidationDatesUpdate(CentraUpdate):
    def update(self):
        pass

class CollectionsUpdate(CentraUpdate):
    def update(self):
        pass

class OrderUpdatesView(BaseView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self,request, *args, **kwargs):
        logger.info("updated orders with discount coupon related info")
        centraOrdersUpdate(message="Centra orders update")
        return JsonResponse({"will be updated in an hour":True},status=200)




class InfluencerView(BaseView):
    pass


class Influencers(BaseView):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        rows = []
        filterDuplicates = False
        fields = self.model._meta.get_fields()
        if request.FILES:
            csv_file = request.FILES['myfile']
            rows = list(csv.DictReader(io.StringIO(csv_file.read().decode('ISO-8859-1'))))
        else:
            rows = json.loads(request.body)

        # Validation for non emopty
        mandatoryFields = influencer_mandatory_fields
        index = 0
        messages = []
        emailValidationRE = "^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$"
        for row in rows:

            index += 1
            for key, value in row.items():
                if key in mandatoryFields and not value.strip():
                    messages.append(key + " is mandatory at row: {0};\n".format(index))
                if key == 'Email':
                    try:

                        match = re.match(emailValidationRE,value)
                        if not match:
                            raise email_validator.EmailNotValidError("Not a proper email format")
                    except email_validator.EmailNotValidError as err:
                        messages.append(key + "  "+value+" : "+err.__str__()+" at row: {0};\n".format(index))
                elif "date" in key.lower():
                    try:
                        test = value = datetime.fromisoformat(value).date()
                    except Exception as e:
                        messages.append(key + "  " + value + " : " + e.__str__() + " at row: {0};\n".format(index))
        if len(messages) > 0:
            try:
                raise ValidationError(messages)
            except ValidationError as  err:
                logger.error(err.messages)
                return JsonResponse({"error": err.messages}, status=500)

        emailsInRows = map(lambda x: x['Email'], rows)
        if 'filterDuplicates' in request.GET and request.GET['filterDuplicates'] == 'true':
            filterDuplicates = True
        duplicates = []
        createdLeadsCount = 0
        statusJSON = dict()
        with transaction.atomic():
            fields = self.model._meta.get_fields()
            for row in reversed(rows):
                matchedDBLead = None

                model = self.model()
                for field in fields:
                    if field.verbose_name in row and row[field.verbose_name].strip():
                        value = None
                        if "_on" in field.attname:
                            value = datetime.fromisoformat(row[field.verbose_name]).date()

                        elif field.get_internal_type() in ['FloatField','IntegerField']:
                            _value = row[field.verbose_name].replace(",","").replace("kr","").replace(" ","")
                            logger.info("value is {0}".format(_value))
                            if _value:
                                value = _value
                        else:
                            value = row[field.verbose_name]
                        logger.info("key {0}and value {1}".format(field.attname, row[field.verbose_name]))
                        model.__setattr__(field.attname, value)

                model.created_by = request.user
                model.updated_by = request.user
                model.save()
                createdLeadsCount += 1

        duplicates.reverse()
        statusJSON['duplicates'] = duplicates
        statusJSON['createdCount'] = createdLeadsCount
        return JsonResponse(statusJSON, safe=False, status=201)






@login_required()
def index(request):
    context = dict()
    countries = Constants.objects.filter(Q(key='countries')).values('value')[0]['value']
    context['countries'] = countries
    collections = Constants.objects.filter(Q(key='collections')).values('value')[0]['value']
    context['collections'] = collections
    channels = Constants.objects.filter(Q(key='chaneels')).values('value')[0]['value']
    context['channels'] = channels
    context["is_user_staff"] = request.user.is_staff
    context["username"] = request.user.get_username()
    context["first_name"]= request.user.get_first_name
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
    countries = Constants.objects.filter(Q(key='countries')).values('value')[0]['value']
    context['list_of_countries'] = countries
    collections = Constants.objects.filter(Q(key='collections')).values('value')[0]['value']
    context['collections'] = collections
    channels = Constants.objects.filter(Q(key='channels')).values('value')[0]['value']
    context['channels'] = channels
    context["is_user_staff"] = request.user.is_staff
    context["username"] = request.user.get_username()
    context["first_name"] = request.user.first_name
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
    item['updated_by__username'] = x.created_by.username
    item['updated_by__username'] = x.updated_by.username
    item['created_by__first_name'] = x.created_by.first_name
    item['created_by__last_name'] = x.created_by.last_name
    item['updated_by__first_name'] = x.updated_by.first_name
    item['updated_by__last_name'] = x.updated_by.last_name
    return item


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
                          'created_by__first_name',
                          'created_by__last_name',
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
                          "updated_by__username", "updated_by__first_name",  "updated_by__last_name")

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




