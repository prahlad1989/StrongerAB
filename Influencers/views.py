import codecs
import csv
import io
from collections import Set
from functools import reduce

import email_validator
import itertools
import json
import logging
from datetime import datetime, timedelta, date, timezone

from background_task import background
from django.contrib.auth import login, logout as log_out
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction, connection
from django.db.models import Q, Count, Sum
from django.forms import forms, model_to_dict
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, StreamingHttpResponse, HttpResponseNotAllowed
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from Influencers.forms import LoginForm, InfluencerForm
from Influencers.models import Influencer as InfluencerModel, Constants as Constants, OrderInfo, UserPreferences as UserPreferencesModel
from Influencers.tasks import valiationsUpdate
from background_task.models import Task

from StrongerAB1.settings import LEADSPAN, ADMINSPAN, influencer_post_status, paid_unpaid_choices, \
    is_influencer_choices, is_answered_choices
from StrongerAB1.settings import adminMsg
from StrongerAB1.settings import b2b_mandatory_fields
from StrongerAB1.settings import influencer_mandatory_fields
import re

from .SalesInfo import SalesInfo
from .tasks import centraOrdersUpdate,centraToDBFun
logger = logging.getLogger(__name__)



sql_datetime_format = "%Y-%m-%d %H:%M:%S"
javascript_iso_format = ""
sql_date_format = "%Y-%m-%d"
class Index(TemplateView):
    template_name = 'index.html'

def reportPage(request):
    args = dict()
    return render(request, 'report.html',args)

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
    @method_decorator(login_required)
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

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = self._getForm(request)
        #logger.info("form is {0}".format(form))f
        logger.error("form errors {0}".format(form.errors))
        #check if prospect already record exists with email
        messages = []
        object = form.save(commit=False)
        if object.channel_username and object.is_influencer and object.is_influencer == is_influencer_choices[1] and InfluencerModel.objects.filter(Q(channel_username=object.channel_username)).exists():
                messages.append("Instagram Username with username: " + object.channel_username + " " + "already exists")
        if len(messages) > 0:
            try:
                raise ValidationError(messages)
            except ValidationError as  err:
                logger.error(err.messages)
                return JsonResponse({"error": err.messages}, status=500)

        rows = self.model.objects.filter(Q(email__iexact=object.email) )
        if rows and len(rows) > 0:
            object.is_duplicate = True
        object.created_by = request.user
        object.updated_by = request.user
        object.updated_at = datetime.now()
        object.managed_by_id = int(request.POST['managed_by_id'])
        object.date_of_promotion_at = datetime.fromtimestamp(int(request.POST['date_of_promotion_at']),tz=timezone.utc)
        object.save()
        logger.info(
            "Row with username {0} saved by user {1}".format(object.channel_username, request.user.get_username()))
        return HttpResponse(status=201, content=object)

    @method_decorator(login_required)
    def put(self, request, *args, **kwargs):
        item = json.loads(request.body)
        id = item['id']
        index = item['index']
        itemFromDB = self.model.objects.get(pk=id)
        if itemFromDB.created_by_id != request.user.pk and not request.user.is_staff:
            return JsonResponse({'error': "You can't modify Others' Influencers" + adminMsg}, status=500)

        for field in itemFromDB._meta.fields:
            if field.name in item and "_on" in field.name and item[field.name]:
                date = item[field.name]
                try:
                    date = datetime.fromtimestamp(item[field.name])
                    itemFromDB.__setattr__(field.name, date)
                except Exception as e:
                    logger.exception(e)
                    if(item[field.name].find("Z")> -1):
                        date = datetime.strptime(item[field.name], "%Y-%m-%dT%H:%M:%SZ").astimezone(timezone.utc)
                        itemFromDB.__setattr__(field.name, date)
                    else:
                        date = datetime.strptime(item[field.name], "%Y-%m-%d").astimezone(timezone.utc)
                        itemFromDB.__setattr__(field.name, date)


            elif field.name in item and not field.name in ['created_by','updated_by','influencerbase_ptr','revenue_click','managed_by']:
                #print(field.name)
                itemFromDB.__setattr__(field.name, item[field.name])
        itemFromDB.updated_by = request.user
        itemFromDB.managed_by_id = item['managed_by_id']
        itemFromDB.updated_at = datetime.now()
        itemFromDB.save()
        logger.info(
            "Record with influencer name {1} updated by user {0}".format(request.user.get_username(),
                                                                    itemFromDB.channel_username))
        itemFromDB = leadToDict(itemFromDB)
        itemFromDB['index'] = index
        return JsonResponse(itemFromDB, safe=False, status=200)



class UserPreferences(BaseView):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            obj = UserPreferencesModel()
            obj.influe_field_preferences = data;
            obj.created_by = request.user
            obj.updated_by= request.user
            obj.save()
            return HttpResponse("updated prefs",201)
        except Exception as e:
            logger.error(e)
            return HttpResponse("bad request", status=500)

    @method_decorator(login_required)
    def put(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            obj = UserPreferencesModel.objects.get(created_by=request.user)
            obj.influe_field_preferences = data;
            obj.created_by = request.user
            obj.updated_by= request.user
            obj.save()
            return HttpResponse("updated prefs", 201)
        except Exception as e:
            logger.error(e)
            return HttpResponse("bad request", status=500)

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

class CentraBase(BaseView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class ResetCentra(CentraBase):
    def get(self,request, *args, **kwargs):
        Task.objects.all().delete()
        Constants.objects.filter(key='last_sync_at').delete()
        OrderInfo.objects.all().delete()
        from StrongerAB1.settings import centra_api_start_date
        start_date = datetime.strptime(centra_api_start_date, "%Y-%m-%d").astimezone(timezone.utc)
        InfluencerModel.objects.filter(valid_from__gte =start_date).update(valid_from=None, valid_till= None, revenue_click=None)
        logger.info("deleted all background tasks, last sync, orderinfo, discount code validations")
        return JsonResponse({"Reset centra": True}, status=200)


class CentraToDB(CentraBase):
    def deleteTasks(self, name):
        existing_tasks = Task.objects.all().filter(task_name=name).delete()
        logger.info(existing_tasks[0])
        logger.info("deleted {0} existing tasks with name {1}".format( existing_tasks[0],name))

    def get(self,request, *args, **kwargs):
        logger.info("updated DB with order info")
        self.deleteTasks("Influencers.tasks.centraToDBFun")
        centraToDBFun(message="Centra to DB", repeat =60*60)
        return JsonResponse({"will be updated in an hour":True},status=200)



class ValidationUpdatesView(CentraToDB):
    def get(self,request, *args,**kwargs):
        logger.info("updating influencers with discount coupon related info{0}".format(datetime.now()))
        self.deleteTasks("Influencers.tasks.valiationsUpdate")
        valiationsUpdate(message="Centra coupon validations update", repeat =3000)
        return JsonResponse({"coupon codes be updated in an hour":True},status=200)

class InfluencerView(BaseView):
    pass

class Influencers(BaseView):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(login_required)
    def delete(self, request, *args, **kwargs):
        try:
            influes_tobe_deleted = json.loads(request.body)
            deletedRows = self.model.objects.filter(id__in= influes_tobe_deleted).delete()
            deletedRows=round(deletedRows[0] / 2)
            return JsonResponse("deleted {0} records".format(deletedRows),safe=False,status=200)
        except Exception as e:
            logger.error(e)
            return JsonResponse({"error":"Some issue at deletion"}, status=500)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        rows = []
        filterDuplicates = False
        fields = self.model._meta.get_fields()
        if request.FILES:
            csv_file = request.FILES['myfile']
            file_contents = csv_file.read().decode('utf-8')
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(file_contents)
            rows = list(csv.DictReader(io.StringIO(file_contents),dialect=delimiter))
        else:
            rows = json.loads(request.body)

        # Validation for non emopty
        mandatoryFields = influencer_mandatory_fields
        index = 0
        messages = []
        #striping all the data by removing spaces
        def y(row):
            rowDict = dict()
            for key, value in row.items():
                rowDict[key.strip()] = value.strip()
            return rowDict;

        rows = list(map(lambda x:y(x),rows))
        isHeadersChecked = False
        for row in rows:
            if not isHeadersChecked:
                isHeadersChecked = True
                rowKeysSet = set(row.keys())
                mandatoryKeysSet = set(mandatoryFields)
                missingMandatoryFields = mandatoryKeysSet.difference(rowKeysSet)
                if missingMandatoryFields:
                    messages.append("missing mandatory headers {0}".format(missingMandatoryFields))
                    break


            index += 1
            for key, value in row.items():
                if key in mandatoryFields and not value:
                    messages.append(key + " is mandatory at row: {0};\n".format(index))
                elif ("date" in key.lower() or "day" in key.lower()) and value :
                    try:
                        value = datetime.fromisoformat(value).date()
                    except Exception as e:
                        messages.append(key + "  " + value + " : " + e.__str__() + " at row: {0};\n".format(index))
                elif key in ['Manager']:
                    try:
                        isUserExists = User.objects.get(username=value)
                    except Exception as e:
                        messages.append(key + "  " + value + " : " + e.__str__() + " at row: {0};\n".format(index))
                for x in [InfluencerModel.followers_count, InfluencerModel.commission, InfluencerModel.product_cost, InfluencerModel.revenue_analysis, InfluencerModel.revenue_click]:
                    field = InfluencerModel._meta.get_field(x.field_name)
                    if key == field.verbose_name and value:
                        try:
                            value = re.sub("[^\d,]","",value) #filtering shitty values which have 'kr', space, and commas in values
                            value = re.sub(",", ".", value)
                            value = float(value)
                        except Exception as e:
                            messages.append(key + "  " + value + " : " + "can't convert to number"+ " at row: {0};\n".format(index))
                for x in [InfluencerModel.comments, InfluencerModel.order_num, InfluencerModel.order_code, InfluencerModel.discount_coupon ,InfluencerModel.channel,InfluencerModel.paid_or_unpaid]:
                    field = InfluencerModel._meta.get_field(x.field_name)
                    if key == field.verbose_name and value and len(value) > field.max_length:
                        messages.append(
                            "for " + key + "  " + value + " : " + "should not be more than {0} chars at row: {1};\n".format(
                                field.max_length, index))

                #
                #     if len(value) > 500:
                #         messages.append(
                #             "for " + key + "  " + value + " : " + "should not be more than 500 chars at row: {0};\n".format(
                #                 index))

        if len(messages) > 0:
            try:
                raise ValidationError(messages)
            except ValidationError as  err:
                logger.error(err.messages)
                return JsonResponse({"error": err.messages}, status=422)

        index =0
        for row in rows:
            index += 1
            channel_username = row.get('Instagram Username')
            is_influencer_prospect = row['Influencer/Prospect']
            if channel_username and is_influencer_prospect and is_influencer_prospect == is_influencer_choices[1]:
                if InfluencerModel.objects.filter(Q(channel_username = channel_username)).exists():
                     messages.append("Instagram Username  " + channel_username + " : " + "already existed at row: {0};\n".format(index))

        if len(messages) > 0:
            try:
                raise ValidationError(messages)
            except ValidationError as  err:
                logger.error(err.messages)
                return JsonResponse({"error": err.messages}, status=422)

        emailsInRows = map(lambda x: x['Email'], rows)
        if request.GET.get('filterDuplicates') == 'true':
            filterDuplicates = True
        duplicates = []
        createdLeadsCount = 0
        statusJSON = dict()
        try:
            with transaction.atomic():
                fields = self.model._meta.get_fields()
                for row in reversed(rows):
                    model = self.model()
                    for field in fields:
                        if field.verbose_name in row and row[field.verbose_name].strip():
                            value = None
                            if "_on" in field.attname:
                                value = datetime.fromisoformat(row[field.verbose_name]).date()
                            elif "_at" in field.attname:
                                value = datetime.fromisoformat(row[field.verbose_name])
                            elif field.get_internal_type() in ['FloatField','IntegerField']:
                                _value = row[field.verbose_name]
                                _value = re.sub("[^\d,]", "", _value)
                                _value = re.sub(",", ".", _value)
                                _value = float(_value)
                                #logger.info("value is {0}".format(_value))
                                if _value:
                                    value = _value
                            elif field.attname in ["managed_by_id"]:
                                value = row[field.verbose_name]
                                value = User.objects.get(username=value).id
                            else:
                                value = row[field.verbose_name].strip()
                            #logger.info("key {0}and value {1}".format(field.attname, row[field.verbose_name]))
                            model.__setattr__(field.attname, value)

                    model.created_by = request.user
                    model.updated_by = request.user
                    model.updated_at = datetime.now()
                    model.save()
                    createdLeadsCount += 1
        except Exception as e:
            logger.error(e.__str__())
            return JsonResponse({"error": e.__str__()}, status=500)
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
    user = request.user
    context = dict()
    countries = Constants.objects.filter(Q(key='countries')).values('value')[0]['value']
    context['list_of_countries'] = countries
    collections = Constants.objects.filter(Q(key='collections')).values('value')[0]['value']
    context['collections'] = collections
    channels = Constants.objects.filter(Q(key='channels')).values('value')[0]['value']
    context['channels'] = channels
    context["is_user_staff"] = user.is_staff
    context["username"] = user.get_username()
    context["first_name"] = user.first_name
    context["user_id"] = user.id
    influencerFields = InfluencerModel._meta.get_fields()
    influencerFieldsList = list()
    influencerFieldsDict = dict()
    for field in influencerFields:
        influencerFieldsDict[field.attname] = field.verbose_name
        influencerFieldsDict[field.verbose_name] = field.attname
        influencerFieldsList.append(field.verbose_name)
    context["influencerFieldsDict"] = influencerFieldsDict
    context["influencer_post_status"] = influencer_post_status
    context["paid_unpaid_choices"] = paid_unpaid_choices
    context["is_influencer_choices"] = is_influencer_choices
    context["is_answered_choices"] = is_answered_choices
    context["influencer_mandatory_fields"] = influencer_mandatory_fields
    context["influencerFieldsList"]= influencerFieldsList
    context['influe_field_preferences'] = getUserPrefs(user)
    context['users'] = getUserNames()
    return render(request, 'Influencer.html', context)


# helper class; not related to view directly
class Echo:
    def write(self, value):
        return value

def getUserNames():
    users = User.objects.order_by(User.first_name.field_name).values('username','first_name','last_name','id')
    users = map(lambda  x:{'username': x['username'], 'full_name': x['first_name']+" "+x['last_name'], 'id':x['id']},users)
    result = [{'username': '', 'full_name': '','id':''}]
    result.extend(users)
    return result
    #return JsonResponse({"users": list(usernames)}, safe=False, status=200)


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
    item['created_by__first_name'] = x.created_by.first_name
    item['created_by__last_name'] = x.created_by.last_name
    item['updated_by__first_name'] = x.updated_by.first_name
    item['updated_by__last_name'] = x.updated_by.last_name
    item['managed_by__first_name'] = x.managed_by.first_name
    item['managed_by__last_name'] = x.managed_by.last_name
    item['managed_by_id'] = x.managed_by.id

    return item


#Influencer query

def getUserPrefs(user):
    try:
        obj = UserPreferencesModel.objects.get(created_by=user)
        return obj.influe_field_preferences
    except Exception as e:
        return []
        logger.info("usef prefs for {0} not exists yet".format(user.get_username()))


class InfluencersQuery(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    model = InfluencerModel

    def getDateFields(self):
        return []
        # fields = self.model._meta.get_fields()
        # for field in fields:
    fields_in_response = ('id',
                          InfluencerModel.is_influencer.field_name,
                          'created_by__username',
                          'created_by__first_name',
                          'created_by__last_name',
                          'created_by__id',
                          InfluencerModel.email.field_name,
                          InfluencerModel.is_answered.field_name,
                          InfluencerModel.is_duplicate.field_name,
                          InfluencerModel.order_num.field_name,
                          InfluencerModel.order_code.field_name,
                          InfluencerModel.date_of_promotion_at.field_name,
                          InfluencerModel.influencer_name.field_name,
                          InfluencerModel.paid_or_unpaid.field_name,
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
                          InfluencerModel.is_old_record.field_name,
                          InfluencerModel.created_at.field_name,
                          InfluencerModel.updated_at.field_name,
                          InfluencerModel.centra_update_at.field_name,
                          "updated_by__id", "updated_by__username", "updated_by__first_name",  "updated_by__last_name",
                          "managed_by_id", "managed_by__username", "managed_by__first_name",  "managed_by__last_name")


    def getQueryParams(self, request):
        searchParams = dict()
        requestBody = json.loads(request.body)
        for k, v in requestBody.items():
            if isinstance(v, bool) and v:
                searchParams[k] = v

            elif isinstance(v, str) and len(v) > 0:
                if k in ['sortOrder', 'sortField']:
                    searchParams[k] = v
                elif k in ['paid_or_unpaid', 'channel', 'status', 'collection','managed_by_id'] and v:
                    searchParams[k] = v
                elif k in ['created_by','updated_by']:
                    searchParams[k+"__username" + "__icontains"] = v


                else:
                    searchParams[k  + "__icontains"] = v
            elif "_at" in k and v:
                range = v
                start = range.get('start')
                end = range.get('end')
                searchParams[k+'__gte'] = datetime.fromtimestamp(start)
                searchParams[k+'__lte'] = datetime.fromtimestamp(end)+timedelta(1)
            elif k in ['pageIndex', 'pageSize'] and v:
                searchParams[k] = v
            elif k in ['managed_by'] and v:
                searchParams[k+"__id"] = v

            elif "_on" in k and v:
                range = v
                start = range.get('start')
                end = range.get('end')
                searchParams[k+"__gte"] = datetime.fromtimestamp(start).date()
                searchParams[k + "__lte"] = datetime.fromtimestamp(end).date() + timedelta(1)
            elif k and "__username" not in k and "managed_by_id" not in k and self.model._meta.get_field(k).get_internal_type() == "DateTimeField" and v:
                range = v
                start = range.get('start')
                end = range.get('end')
                searchParams[k+"__gte"] = datetime.fromtimestamp(start)
                searchParams[k + "__lte"] = datetime.fromtimestamp(end)


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



class SalesReport(View):
    def get(self,request,*args,**kwargs):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # start_date = datetime.today()-timedelta(100)
        # end_date = datetime.today()
        # if not start_date and not end_date:
        #     return HttpResponse("Invalid input",status=404)
        # else:
        #     start_date = datetime.fromtimestamp(start_date,tz=timezone.utc)
        #     end_date = datetime.fromtimestamp(end_date,tz=timezone.utc)

        if not start_date or not end_date:
             return render(request, 'report.html',None)
        start_date = datetime.fromtimestamp(int(start_date), tz=timezone.utc)
        end_date = datetime.fromtimestamp(int(end_date), tz= timezone.utc)
        #influe_vouchers = InfluencerModel.objects.values(InfluencerModel.discount_coupon.field_name).distinct()
        country_sales_vouchers_dict= dict() # to use just for quick look up of grandtotal of countries
        rows = []
        cursor = connection.cursor()
        try:
            query = "select o1.country, sum(o1.\"grandTotal\") as voucher_sales from public.\"Influencers_influencer\" i1 inner join public.\"Influencers_orderinfo\" o1 on i1.discount_coupon=o1.discount_coupons  and o1.\"orderDate\" >= \'{0}\' and o1.\"orderDate\" <= \'{1}\' group by o1.country having sum(o1.\"grandTotal\") >0 ".format(start_date.strftime(sql_date_format),end_date.strftime(sql_date_format))
            cursor.execute(query)
            while True:
                row = cursor.fetchone()
                country_sales_vouchers_dict[row[0]] = row[1]
        except Exception as e:
            logger.exception(e.__str__())
        finally:
            cursor.close()

        cursor = connection.cursor()
        try:
            costs_query = "select i1.country, sum(i1.product_cost) as  product_cost, sum(i1.commission) as commission from  public.\"Influencers_influencer\" i1 where date_of_promotion_at >= \'{0}\' and date_of_promotion_at <= \'{1}\' group by i1.country".format(start_date.strftime(sql_date_format),end_date.strftime(sql_date_format))
            cursor.execute(costs_query)
            while True:
                row = cursor.fetchone()
                country_name = row[0]
                salesInfo = SalesInfo()
                if country_name in country_sales_vouchers_dict:
                    voucher_sales = country_sales_vouchers_dict[country_name]
                    salesInfo.voucher_sales = voucher_sales
                    salesInfo.product_cost = row[1]
                    salesInfo.commission = row[2]
                    salesInfo.total_cost = salesInfo.product_cost + salesInfo.commission
                    # replace the dict value with new sales ifno obj
                    country_sales_vouchers_dict[country_name ] = salesInfo
                    logger.debug("updated commission and product cost")
                else:
                    salesInfo.voucher_sales = 0
                    salesInfo.product_cost = row[1]
                    salesInfo.commission = row[2]
                    salesInfo.total_cost = salesInfo.product_cost + salesInfo.commission
                    country_sales_vouchers_dict[country_name] = salesInfo
                    logger.debug("updated commission and product cost with 0 sales")

        except Exception as e:
            logger.exception(e.__str__())
        finally:
            cursor.close()

        orders = OrderInfo.objects.filter(Q(orderDate__gte=start_date) & Q(orderDate__lte=end_date))
        country_field_name = InfluencerModel.country.field_name
        # entire sales country wise , in the specified time period.
        # this is obtained from orderinfo, i.e from centra sync details
        country_sales = orders.values(country_field_name).annotate(sales=Sum('grandTotal'))

        for _ in country_sales:
            _country_name = _[country_field_name]
            _sales = _['sales']
            if type(country_sales_vouchers_dict.get(_country_name)).__name__ == 'SalesInfo':
                salesInfo = country_sales_vouchers_dict[_country_name]
                salesInfo.country = _country_name
                salesInfo.country_sales = _sales
                rows.append(salesInfo)
            elif _country_name in country_sales_vouchers_dict :
                salesInfo = SalesInfo()
                salesInfo.country = _country_name
                voucher_sales = country_sales_vouchers_dict[_country_name] # retrieve from dict
                salesInfo.voucher_sales = voucher_sales
                rows.append(salesInfo)
            else:
                salesInfo = SalesInfo()
                salesInfo.country =_country_name
                salesInfo.country_sales = _['sales']
                rows.append(salesInfo)

        #evalulate total voucher_sales sum
        total_voucher_sales =0
        total_voucher_sales = reduce(lambda x,y:x+y.country_sales,rows, total_voucher_sales)

        for salesInfo in rows:
            if salesInfo.country_sales > 0:
                salesInfo.influe_to_country_sales_ratio = (salesInfo.voucher_sales/salesInfo.country_sales)*100
                salesInfo.influe_to_country_sales_ratio = round(salesInfo.influe_to_country_sales_ratio,2)
            salesInfo.roas = salesInfo.voucher_sales-salesInfo.total_cost
            if total_voucher_sales > 0:
                percent_total_sales = (salesInfo.voucher_sales/total_voucher_sales)*100
                salesInfo.percent_total_sales = round(percent_total_sales, 2)# remove last 2 decimals
        responseObj = dict()
        responseObj['salesInfos'] = list(map(lambda x:x.__dict__, rows))
        return JsonResponse(responseObj, status=200, safe=False)




