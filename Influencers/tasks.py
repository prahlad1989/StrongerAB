import concurrent.futures
import json
import multiprocessing
from datetime import datetime, timedelta
from logging import getLogger

import time
from background_task import background
from django.db import connection
from django.db.models import Q, Min
from django.utils import timezone
from jsonpath_ng import parse
from python_graphql_client import GraphqlClient

from Influencers.models import Influencer as Influencer, Constants, OrderInfo
from StrongerAB1.settings import centra_api_start_date, centra_api_revenue_click_start
from StrongerAB1.settings import centra_key, centra_api_url

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
    graphQlQuery = """ query($orderStartDate: String!, $orderEndDate: String!, $pageNumber: Int!) { orders(where:{status: [CONFIRMED, PARTIAL, SHIPPED, PENDING], orderDate: {from: $orderStartDate, to: $orderEndDate} }, limit: 500, page: $pageNumber, sort: number_ASC  )
                    { orderDate
                     number 
                     createdAt
                     currencyBaseRate
                     status
                     country{
                      ...country_frag
                    } 
                     grandTotal(includingTax: false){ 
                        ...monetary }
                     discountsApplied{
                        date
                        value{...monetary}
                        ...myfrag
                    }

                    } 

                    }
                    fragment country_frag on Country{
                        id
                        name
                        code
                        continent
                        isEU
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

class OrdersUpdate2(OrdersUpdate):
    def update(self):
        cursor = connection.cursor()
        try:
            cursor.execute("update public.\"Influencers_influencer\" as inf set \"centra_update_at\"=now(), revenue_click =(select sum(\"grandTotal\") from public.\"Influencers_orderinfo\" where discount_coupons = inf.discount_coupon and status in ('CONFIRMED', 'PARTIAL', 'SHIPPED', 'PENDING') and inf.valid_from <= \"orderDate\" and inf.valid_till >= \"orderDate\" ) where (select sum(\"grandTotal\") from public.\"Influencers_orderinfo\" where discount_coupons = inf.discount_coupon and status in ('CONFIRMED', 'PARTIAL', 'SHIPPED', 'PENDING') and inf.valid_from <= \"orderDate\" and inf.valid_till >= \"orderDate\" ) is not NULL")

        except Exception as e:
            logger.exception(e.__str__())
        finally:
            cursor.close()
        logger.info("update revenue click complete")


@background(schedule=60*60)
def centraOrdersUpdate(message):
    logger.info('initiated ordersupdate thread: ')
    try:
        logger.debug("order update started at {0}".format(datetime.utcnow()))
        ordersUpdate = OrdersUpdate2()
        ordersUpdate.update()
        logger.debug("order update completed at {0}".format(datetime.utcnow()))
    except Exception as e:
        logger.error(e.__str__())
        logger.exception(e)


class CentraToDB(OrdersUpdate2):
    def sync_orders(self, dateRange, totalOdersDict):
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
            try:
                resp = client.execute(query=graphQlQuery, variables=api_query_params)
                time.sleep(1)
                orders = resp['data']['orders']
                logger.debug("orders  length {0}".format(len(orders)))
                for order in orders:
                    if(not order["discountsApplied"]):
                        continue
                    orderInfo = OrderInfo()
                    orderInfo.number = order['number']
                    logger.debug("order details  {0}".format(order))
                    # if(orderInfo.number in totalOdersDict):
                    #     logger.error("order repeated with {0},{1},{2} with {3}".format( api_query_params["orderStartDate"] ,api_query_params["orderEndDate"], api_query_params['pageNumber']  ,totalOdersDict[orderInfo.number] ))
                    # else:
                    #     totalOdersDict[orderInfo.number] = [api_query_params["orderStartDate"] ,api_query_params["orderEndDate"], api_query_params['pageNumber']]
                    orderInfo.orderDate = order['orderDate']
                    expr = parse('$.discountsApplied[*].discount.code')
                    values = expr.find(order)
                    values = list(map(lambda x: x.value, values))
                    logger.debug("discount coupons {0} ".format(values))
                    if not values[0]:
                        logger.debug("has no discounts")
                        continue
                    orderInfo.discount_coupons = values[0]
                    orderInfo.status = order["status"]
                    orderInfo.grandTotal = round(order["grandTotal"]["value"]*order["currencyBaseRate"])
                    orderInfoList.append(orderInfo)
                if orders:
                        api_query_params['pageNumber'] = api_query_params['pageNumber'] + 1
                        logger.debug("pageNumber incremented to {0}".format(api_query_params['pageNumber']))
                        logger.debug("trying to bulk insert")
                        OrderInfo.objects.bulk_create(orderInfoList)
                        logger.info("created {0} objects".format(len(orderInfoList)))
                        orderInfoList.clear()
                else:
                    logger.info("processed all orders for a thread.")
                    break
            except Exception as e:
                logger.exception(e)
                raise e


    def update(self):
        tic = time.time()
        last_sync_at = Constants.objects.filter(key='last_sync_at')
        if last_sync_at:  # remembering the last sync done with centra  so that we can process from there.
            last_sync_at = last_sync_at[0].value
            last_sync_at = datetime.strptime(last_sync_at, self.timeFormat ).astimezone(timezone.utc)
            logger.debug("last processed order exists as {0} ".format(last_sync_at))
        else:
            logger.debug("not processed previously")
            last_sync_at = datetime.strptime( centra_api_start_date,"%Y-%m-%d").astimezone(timezone.utc)
        now = datetime.now().astimezone()
        delta = (now-last_sync_at).total_seconds()
        num_of_threads = 10
        temp_delta = int(delta/num_of_threads) # for each call,
        totalOrdersDict = dict()
        start_and_end_dates = [(last_sync_at+timedelta(seconds=1+ i*temp_delta), last_sync_at+timedelta(seconds=(i+1)*temp_delta)) for i in range(num_of_threads)]
        with concurrent.futures.ThreadPoolExecutor(num_of_threads) as executor:
            results = [executor.submit(self.sync_orders, dateRange, totalOrdersDict) for dateRange in start_and_end_dates]

        c = Constants.objects.filter(key='last_sync_at');
        if not c:
            logger.info("updating last sync after centra reset")
            c= Constants()
            c.key="last_sync_at"
            c.value=now.strftime(self.timeFormat)
            c.save()
        else:
            c = c[0]
            c.value=now.strftime(self.timeFormat)
            c.save()
        logger.info("time taken for total orders sync {0}".format(int(time.time()-tic)))


        logger.info("now started updating influencers revenue click")
        cursor = connection.cursor()

        query = "update public.\"Influencers_influencer\" as inf set \"centra_update_at\"=now(), revenue_click =(select sum(\"grandTotal\") from public.\"Influencers_orderinfo\" where discount_coupons = inf.discount_coupon and status in ('CONFIRMED', 'PARTIAL', 'SHIPPED', 'PENDING') and inf.valid_from <= \"orderDate\" and inf.valid_till >= \"orderDate\" and inf.date_of_promotion_on > \'{0}\' and inf.date_of_promotion_on >= inf.valid_from and date_of_promotion_on <= inf.valid_till ) where (select sum(\"grandTotal\") from public.\"Influencers_orderinfo\" where discount_coupons = inf.discount_coupon and status in ('CONFIRMED', 'PARTIAL', 'SHIPPED', 'PENDING') and inf.valid_from <= \"orderDate\" and inf.valid_till >= \"orderDate\" and inf.date_of_promotion_on > \'{1}\' and inf.date_of_promotion_on >= inf.valid_from and date_of_promotion_on <= inf.valid_till) is not NULL".format(centra_api_revenue_click_start, centra_api_revenue_click_start)

        try:
            cursor.execute(query)
        except Exception as e:
            logger.exception(e.__str__())
        finally:
            cursor.close()
        logger.info("update revenue click complete")



class CentraToDBAllOrders(CentraToDB):
    def sync_orders(self, dateRange, totalOdersDict):
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
            try:
                resp = client.execute(query=graphQlQuery, variables=api_query_params)
                time.sleep(1)
                orders = resp['data']['orders']
                logger.debug("orders  length {0}".format(len(orders)))
                for order in orders:
                    orderInfo = OrderInfo()
                    orderInfo.number = order['number']
                    orderInfo.status = order["status"]
                    orderInfo.country = order['country']['name']
                    orderInfo.grandTotal = round(order["grandTotal"]["value"]*order["currencyBaseRate"])
                    logger.debug("order details  {0}".format(order))
                    orderInfo.orderDate = order['orderDate']
                    if order["discountsApplied"]:
                        expr = parse('$.discountsApplied[*].discount.code')
                        values = expr.find(order)
                        values = list(map(lambda x: x.value, values))
                        logger.debug("discount coupons {0} ".format(values))
                        if not values[0]:
                            logger.debug("has no discounts")
                            continue
                        orderInfo.discount_coupons = values[0]

                    orderInfoList.append(orderInfo)
                if orders:
                        api_query_params['pageNumber'] = api_query_params['pageNumber'] + 1
                        logger.debug("pageNumber incremented to {0}".format(api_query_params['pageNumber']))
                        logger.debug("trying to bulk insert")
                        OrderInfo.objects.bulk_create(orderInfoList)
                        logger.info("created {0} objects".format(len(orderInfoList)))
                        orderInfoList.clear()
                else:
                    logger.info("processed all orders for a thread.")
                    break
            except Exception as e:
                logger.exception(e)
                raise e




@background(schedule=1*60)
def centraToDBFun(message):
    logger.info('initiated db from centra update')

    centraToDB  = CentraToDBAllOrders()
    try:
        tic = time.time()
        logger.debug("DB update started at {0}".format(datetime.utcnow()))
        centraToDB.update()
        logger.debug("DB update completed at {0}".format(datetime.utcnow()))
        logger.info("time taken for DB update is {0}".format(int(time.time()-tic)))
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
                api_query_params['couponCode'] = discount_coupon = eachObj.discount_coupon
                resp = client.execute(query=graphQlQuery, variables=api_query_params)
                coupons = resp["data"]["discounts"]
                for coupon_from_api in coupons:
                    if coupon_from_api['code'] ==  discount_coupon:
                        logger.debug("coupon details are {0}".format(coupon_from_api))
                        eachObj.valid_from = datetime.strptime(coupon_from_api['startAt'], self.timeFormat).astimezone(
                            timezone.utc)
                        eachObj.valid_till = datetime.strptime(coupon_from_api['stopAt'], self.timeFormat).astimezone(
                            timezone.utc)
                        # eachObj.centra_update_at = datetime.now(tz=timezone.utc)
                        logger.debug("copon: {0},start time: {1}, and end time: {2}".format(coupon_from_api, eachObj.valid_from,
                                                                                            eachObj.valid_till))
                        eachObj.save()
                        break
            except Exception as e:
                logger.error("error with object{0} ".format(eachObj))
                logger.exception(e)

        logger.info("time taken for total coupon updates {0}".format((int(time.time() - tic))))


@background(schedule=2*60*60)
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

