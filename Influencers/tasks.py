import concurrent.futures
import json
import multiprocessing
from functools import reduce

from background_task import background
from logging import getLogger

import requests
from django.db import transaction
from django.db.models import Q, Min

from StrongerAB1.settings import centra_key, centra_api_url
from Influencers.models import Influencer as Influencer, Constants, OrderInfo
from datetime import date, datetime, timedelta
import time

from jsonpath_ng import jsonpath, parse
from django.utils import timezone
from python_graphql_client import GraphqlClient
from StrongerAB1.settings import centra_api_start_date
logger = getLogger(__name__)


headers={'Authorization': 'Bearer '+str(centra_key),  'Content-Type': 'application/json' }
class CentraUpdate:
    def update(self):
        pass

    today = datetime.now(tz=timezone.utc)
    timeFormat = "%Y-%m-%dT%H:%M:%S%z"
    graphQlQuery =""
    client = GraphqlClient(endpoint=centra_api_url, headers=headers)


class OrdersUpdate(CentraUpdate):
    graphQlQuery = """ query($orderStartDate: String!, $orderEndDate: String!, $pageNumber: Int!) { orders(where:{status: [CONFIRMED, PARTIAL, SHIPPED], orderDate: {from: $orderStartDate, to: $orderEndDate} }, limit: 5000, page: $pageNumber, sort: number_ASC  )
                    { orderDate
                     number 
                     createdAt
                     currencyBaseRate
                     status 
                     grandTotal{ 
                        ...monetary }
                     discountsApplied{
                        date
                        value{...monetary}
                        ...myfrag
                    }

                    } 

                    }

                    fragment monetary on MonetaryValue { 
      										value 
                          currency {code } 
                          formattedValue
                        }
                    fragment myfrag on AppliedDiscount{
                                  discount{
                                    id
                                    status
                                    name
                                    method
                                    type
                                    code
                                    startAt
                                    stopAt
                                  }
                    } """


    def update(self):
       # Read all the influencers table in the last one month or read each row which have coupon code validation greater than today.
       #  pick each coupon's start date and end date.
       #  read all the orders in that time span , check if the each order discount has that coupon. Then , update the DB of the influencer.
       #  Read each of the


        #select oldest coupon code which is still valid currently.


        valid_till_filter = Q(valid_till__gte = self.today) # format to be done later
        query = Influencer.objects.filter(valid_till_filter).aggregate(Min('valid_from'))
        #startDate = query['valid_from__min'].date().__str__() # why needed?
        influencersList = list(Influencer.objects.filter(valid_till_filter))

        graphQlQuery = self.graphQlQuery
        client = self.client

        api_query_params = {}
        api_query_params['pageNumber'] = 1
        api_query_params["orderEndDate"] = self.today.strftime(self.timeFormat)
        lastProcessedOrderNum =0
        lastProcessedOrderDate=""
        lastProcessedOrder = Constants.objects.filter(key = 'lastProcessedOrder')
        allCouponCodes = {}
        if lastProcessedOrder: # remembering the last processed order so that we can process from there.

            lastProcessedOrder = lastProcessedOrder[0]
            order = json.loads(lastProcessedOrder.value)
            logger.debug("last processed order exists as {0} ".format(order))
            api_query_params['orderStartDate'] = order['orderDate']
            lastProcessedOrderNum = order['number']
        else:
            logger.debug("no last processed order")
            lastProcessedOrderNum =0
            api_query_params['orderStartDate']= lastProcessedOrderDate = centra_api_start_date

        tic= time.time()
        while True:

            resp = client.execute(query=graphQlQuery, variables=api_query_params)
            orders = resp['data']['orders']
            for order in orders:
                if order['number'] == lastProcessedOrderNum:
                    logger.info("bit of repeating.this order is already processed")
                    continue
                logger.info("order info {0}".format(order))
                expr = parse('$.discountsApplied[*].discount.code')
                values = expr.find(order)
                values = list(map(lambda x: x.value, values))
                if values:
                    logger.info("coupon codes in order#{0} are {1}".format(order['number'], values))
                    #influencersList = Influencer.objects.filter(valid_till_filter)

                    for eachObj in influencersList:
                        try:
                            coupon = eachObj.discount_coupon
                            if coupon and coupon in values:
                                # logger.info("coupon {0} of influencer {1} found in order {2} so updating with price+ {3}", coupon, "created", order['number'], order['grandTotal']['value'])
                                logger.info("coupon {0} of influencer {1} found in order {2} so updating with price+ {3} with currency{4} with exchange rate{5}".format(
                                coupon, "created", order['number'], order['grandTotal']['value'], order['grandTotal']['currency']['code'], order['currencyBaseRate']))
                                revenueGenerated = order['grandTotal']['value'] * order['currencyBaseRate']
                                logger.info("previous revenue of coupon{0} is {1} ".format(coupon,eachObj.revenue_click))
                                if revenueGenerated:
                                    eachObj.revenue_click += revenueGenerated
                                    logger.info("revenue click generated for coupon{0} is {1}".format(coupon, revenueGenerated))
                                    #eachObj.centra_update_at = datetime.now(tz=timezone.utc)
                                    eachObj.save()
                            else:
                                logger.info("our coupon not found in order {0}".format(order['number']))
                        except Exception as e:
                            logger.error("error with object{0} ".format(eachObj))
                            logger.exception(e)

                else:
                    logger.info("no coupon codes in order {0}".format(order))
            logger.info("time taken for {0} number of orders orders {1}".format(len(orders),int(time()-tic)))
            if orders :
                api_query_params['pageNumber'] = api_query_params['pageNumber']+1
                logger.debug("pageNumber incremented to {0}".format(api_query_params['pageNumber']))
                lastOrder = orders[len(orders)-1]
                lastOrder = {"number": lastOrder["number"], "orderDate": lastOrder["orderDate"]}
                if lastProcessedOrder:
                    pass
                else:
                    lastProcessedOrder = Constants()
                    lastProcessedOrder.key = "lastProcessedOrder"
                lastProcessedOrder.value = json.dumps(lastOrder)
                logger.info("saving last order values as {0} ".format(lastOrder))
                lastProcessedOrder.save()
            else:
                logger.info("processed all orders. Done for now")
                break
        logger.error("time taken for total orders in a day orders orders {0}".format(int(time()-tic)))


class OrdersUpdate2(OrdersUpdate):

    def sync_orders(self, influencer):
        graphQlQuery = self.graphQlQuery
        client = self.client
        logger.info(
            "starting order sync for coupon {0} at influencer id {1}".format(influencer.discount_coupon, influencer.id))
        tic = time.time()
        orderEndDate = datetime.utcnow()
        api_query_params = {}
        api_query_params['pageNumber'] = 1
        api_query_params["orderEndDate"] = orderEndDate.strftime(self.timeFormat)
        if influencer.centra_update_at is not None:
            orderStartDate = influencer.centra_update_at + timedelta(
                seconds=1)  # so that you will not get previous orders in response
            api_query_params['orderStartDate'] = orderStartDate.strftime(self.timeFormat)
        else:
            logger.debug("first time update of coupon {0}".format(influencer.discount_coupon))
            orderStartDate = influencer.valid_from
            api_query_params['orderStartDate'] = orderStartDate.strftime(self.timeFormat)
        while True:
            resp = client.execute(query=graphQlQuery, variables=api_query_params)
            orders = resp['data']['orders']
            coupon_revenue_accum = 0;
            for order in orders:
                logger.info("order info {0}".format(order))
                expr = parse('$.discountsApplied[*].discount.code')
                values = expr.find(order)
                values = list(map(lambda x: x.value, values))
                if values:
                    logger.info("coupon codes in order#{0} are {1}".format(order['number'], values))
                    try:
                        coupon = influencer.discount_coupon
                        if coupon and coupon in values:
                            # logger.info("coupon {0} of influencer {1} found in order {2} so updating with price+ {3}", coupon, "created", order['number'], order['grandTotal']['value'])
                            logger.info(
                                "coupon {0} of influencer {1} found in order {2} so updating with price+ {3} with currency{4} with exchange rate{5}".format(
                                    coupon, "created", order['number'], order['grandTotal']['value'],
                                    order['grandTotal']['currency']['code'], order['currencyBaseRate']))

                            revenueGenerated = order['grandTotal']['value'] * order['currencyBaseRate']
                            logger.info("previous iteration revenue of coupon{0} is {1} ".format(coupon,
                                                                                                 influencer.revenue_click))
                            coupon_revenue_accum += revenueGenerated
                            logger.info(
                                "revenue click generated for coupon{0} is {1}".format(coupon, revenueGenerated))
                            # eachObj.centra_update_at = datetime.now(tz=timezone.utc)

                        else:
                            logger.info("our coupon not found in order {0}".format(order['number']))
                    except Exception as e:
                        logger.error("error with object{0} ".format(coupon))
                        logger.exception(e)

                else:
                    logger.info("no coupon codes in order {0}".format(order))

            if orders:
                api_query_params['pageNumber'] = api_query_params['pageNumber'] + 1
                logger.debug("pageNumber incremented to {0}".format(api_query_params['pageNumber']))
            else:
                logger.info("processed all orders. Done for now")
                break

        if coupon_revenue_accum:
            influencer.revenue_click += coupon_revenue_accum
            influencer.centra_update_at = orderEndDate
            influencer.save()
            logger.info("added revenue {0}".format(coupon_revenue_accum))

        toc = time()
        logger.info("time taken for {0} number of orders orders {1}".format(len(orders), int(toc - tic)))



    def update(self):
       # Read all the influencers table in the last one month or read each row which have coupon code validation greater than today.
       #  pick each coupon's start date and end date.
       #  read all the orders in that time span , check if the each order discount has that coupon. Then , update the DB of the influencer.
       #  Read each of the


        #select oldest coupon code which is still valid currently.


        valid_till_filter = ~Q(discount_coupon = "None") # format to be done later
        #startDate = query['valid_from__min'].date().__str__() # why needed?
        influencersList = Influencer.objects.filter(valid_till_filter)
        logger.info("influencerList for orders {0}".format(len(influencersList)))

        with concurrent.futures.ThreadPoolExecutor(10) as executor:
            results = [executor.submit(self.sync_orders, influencer) for influencer in influencersList]




@background(schedule=60*1)
def centraOrdersUpdate(message):
    logger.info('initiated ordersupdate thread: ')

    ordersUpdate  = OrdersUpdate2()
    try:
        logger.debug("order update started at {0}".format(datetime.utcnow()))
        ordersUpdate.update()
        logger.debug("order update completed at {0}".format(datetime.utcnow()))
    except Exception as e:
        logger.error(e.__str__())
        logger.exception(e)


class CentraToDB(OrdersUpdate2):
    def sync_orders(self, dateRange):
        graphQlQuery = self.graphQlQuery
        client = self.client
        orderStartDate = dateRange[0]
        orderEndDate = dateRange[1]
        logger.info(
            "starting order sync for start {0} at end {1}".format(dateRange[0],dateRange[1]))
        tic = time.time()
        api_query_params = {}
        api_query_params['pageNumber'] = 1
        api_query_params["orderStartDate"] = orderStartDate.strftime(self.timeFormat)
        api_query_params["orderEndDate"] = orderEndDate.strftime(self.timeFormat)
        orderInfoList =[]

        while True:
            resp = client.execute(query=graphQlQuery, variables=api_query_params)
            time.sleep(10)
            orders = resp['data']['orders']
            coupon_revenue_accum = 0;
            logger.debug("orders  length {0}".format(len(orders)))
            for order in orders:
                if(not order["discountsApplied"]):
                    continue
                orderInfo = OrderInfo()
                orderInfo.number = order['number']
                orderInfo.orderDate = order['orderDate']
                expr = parse('$.discountsApplied[*].discount.code')
                values = expr.find(order)
                values = list(map(lambda x: x.value, values))
                #orderInfo.discount_coupons = reduce(lambda x,y:x+""+y+",", values, ",")
                orderInfo.discount_coupons = values[0]
                orderInfo.status = order["status"]
                orderInfo.grandTotal = order["grandTotal"]["value"]*order["currencyBaseRate"]
                orderInfoList.append(orderInfo)

            if orders:
                    api_query_params['pageNumber'] = api_query_params['pageNumber'] + 1
                    logger.debug("pageNumber incremented to {0}".format(api_query_params['pageNumber']))
            else:

                OrderInfo.objects.bulk_create(orderInfoList)
                logger.info("created {0} objects".format(len(orderInfoList)))

                logger.info("processed all orders for a thread.")
                break

        toc = time()
        logger.info("time taken for {0} number of orders orders {1}".format(len(orders), int(toc - tic)))

    def update(self):
        last_sync_at = Constants.objects.filter(key='last_sync_at')
        if last_sync_at:  # remembering the last sync done with centra  so that we can process from there.
            last_sync_at = last_sync_at[0].value
            last_sync_at = datetime.strptime(last_sync_at, self.timeFormat ).astimezone(timezone.utc)
            logger.debug("last processed order exists as {0} ".format(last_sync_at))

        else:
            logger.debug("not processed previously")
            last_sync_at = datetime.strptime( centra_api_start_date,"%Y-%m-%d").astimezone(timezone.utc)


        tic = time.time()

        now = datetime.now().astimezone()
        delta = (now-last_sync_at).total_seconds()
        num_of_threads = multiprocessing.cpu_count()
        temp_delta = int(delta/num_of_threads) # for each call,
        start_and_end_dates = [(last_sync_at+timedelta(seconds=1+ i*temp_delta), last_sync_at+timedelta(seconds=(i+1)*temp_delta)) for i in range(num_of_threads)]
        with concurrent.futures.ThreadPoolExecutor(num_of_threads) as executor:
            results = [executor.submit(self.sync_orders, dateRange) for dateRange in start_and_end_dates]
        c = Constants.objects.filter(key='last_sync_at');
        if not c:
            c= Constants()
            c.key="last_sync_at"
            c.value=now.strftime(self.timeFormat)
            c.save()
        else:
            c = c[0]
            c.value=now.strftime(self.timeFormat)
            c.save()
        logger.info("saving sync time at{0}".format(c.value))

@background(schedule=60*1)
def centraToDBFun(message):
    logger.info('initiated db update')

    centraToDB  = CentraToDB()
    try:
        logger.debug("DB update started at {0}".format(datetime.utcnow()))
        centraToDB.update()
        logger.debug("DB update completed at {0}".format(datetime.utcnow()))
    except Exception as e:
        logger.error(e.__str__())
        logger.exception(e)

class CouponValidationUpdate(CentraUpdate):
    graphQlQuery = """ query($couponCode: [String!]){
                        discounts(where:{code: $couponCode}){
                        id
                        status
                        code
                        startAt
                        stopAt

                        }
                        } """

    def update(self):
        influencersList = Influencer.objects.filter(
            ~Q(discount_coupon__regex=r'^(\s)*$') & ~Q(discount_coupon=None) &
            Q(valid_from=None) & Q(valid_till=None) & Q(is_old_record=False))
        logger.info("influencersList length {0} ".format(len(influencersList)))
        graphQlQuery = self.graphQlQuery
        client = self.client
        api_query_params = {}
        tic = time.time()

        for eachObj in influencersList:
            try:
                coupon = eachObj.discount_coupon
                api_query_params['couponCode'] = coupon
                resp = client.execute(query=graphQlQuery, variables=api_query_params)
                coupons = resp["data"]["discounts"]
                if coupons:
                    coupon_from_api = coupons[0]
                    logger.debug("coupon details are {0}".format(coupon_from_api))
                    eachObj.valid_from = datetime.strptime(coupon_from_api['startAt'], self.timeFormat).astimezone(
                        timezone.utc)
                    eachObj.valid_till = datetime.strptime(coupon_from_api['stopAt'], self.timeFormat).astimezone(
                        timezone.utc)
                    #eachObj.centra_update_at = datetime.now(tz=timezone.utc)
                    logger.debug("copon: {0},start time: {1}, and end time: {2}".format(coupon, eachObj.valid_from,
                                                                                       eachObj.valid_till))
                    eachObj.save()

            except Exception as e:
                logger.error("error with object{0} ".format(eachObj))
                logger.exception(e)

        logger.info("time taken for total coupon updates {0}".format((int(time.time() - tic))))


@background(schedule=60*1)
def valiationsUpdate(message):
    logger.info('initiated coupon validations thread')
    couponValidationUpdate  = CouponValidationUpdate()

    try:
        logger.info("coupon validations started at {0}".format(datetime.utcnow()))
        couponValidationUpdate.update()
        logger.info("coupon validations completed at {0}".format(datetime.utcnow()))
    except Exception as e:
        logger.error(e.__str__())
        logger.exception(e)



@background(schedule=100)
def centraCouponsUpdate(message):
    logger.info("coupon validations started")


def demo_task():
    return None


