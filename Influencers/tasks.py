import json

from background_task import background
from logging import getLogger

import requests
from django.db import transaction
from django.db.models import Q, Min

from StrongerAB1.settings import centra_key, centra_api_url
from Influencers.models import Influencer as Influencer, Constants
from datetime import date, datetime, timedelta
from time import time,sleep

from jsonpath_ng import jsonpath, parse
from django.utils import timezone
from python_graphql_client import GraphqlClient
from StrongerAB1.settings import centra_api_start_date
logger = getLogger(__name__)


headers={'Authorization': 'Bearer '+str(centra_key),  'Content-Type': 'application/json' }
class CentraUpdate:
    def update(self):
        pass

class OrdersUpdate(CentraUpdate):
    graphQlQuery = """ query($orderStartDate: String!, $orderEndDate: String!, $pageNumber: Int!) { orders(where:{status: [CONFIRMED, PARTIAL, SHIPPED], orderDate: {from: $orderStartDate, to: $orderEndDate} }, limit: 5000, page: $pageNumber, sort: number_ASC  )
                    { orderDate
                     number 
                     createdAt
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
    client = GraphqlClient(endpoint=centra_api_url, headers=headers)

    def update(self):
       # Read all the influencers table in the last one month or read each row which have coupon code validation greater than today.
       #  pick each coupon's start date and end date.
       #  read all the orders in that time span , check if the each order discount has that coupon. Then , update the DB of the influencer.
       #  Read each of the


        #select oldest coupon code which is still valid currently.

        today = datetime.now(tz=timezone.utc)
        timeFormat = "%Y-%m-%dT%H:%M:%S%z"
        valid_till_filter = Q(valid_till__gte = today) # format to be done later
        query = Influencer.objects.filter(valid_till_filter).aggregate(Min('valid_from'))
        #startDate = query['valid_from__min'].date().__str__() # why needed?
        influencersList = list(Influencer.objects.filter(valid_till_filter))

        graphQlQuery = self.graphQlQuery
        client = self.client

        api_query_params = {}
        api_query_params['pageNumber'] = 1
        api_query_params["orderEndDate"] = today.strftime(timeFormat)
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

        tic= time()
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
                                logger.info("coupon {0} of influencer {1} found in order {2} so updating with price+ {3}".format(
                                coupon, "created", order['number'], order['grandTotal']['value']))
                                revenueGenerated = order['grandTotal']['value']
                                logger.info("previous revenue of coupon{0} is {1} ".format(coupon,eachObj.revenue_click))
                                if revenueGenerated:
                                    eachObj.revenue_click += revenueGenerated
                                    logger.info("revenue click generated for coupon{0} is {1}".format(coupon, revenueGenerated))
                                    eachObj.save()
                        except Exception as e:
                            logger.error("error with object{0} ".format(eachObj))
                            logger.exception(e)
                    else:
                        print("coupon not found in order {0}".format(order['number']))
                else:
                    logger.info("no coupon codes in order {0}".format(order))
            logger.error("time taken for {0} number of orders orders {1}".format(len(orders),int(time()-tic)))
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
        logger.error("time taken for total orders in a day orders orders {0}".format((time()-tic)/1000))



@background(schedule=60*5)
def centraOrdersUpdate(message):
    logger.info('ordersupdate started')

    ordersUpdate  = OrdersUpdate()
    while True:
        logger.debug("order update started at {0}".format(datetime.utcnow()))
        ordersUpdate.update()
        logger.debug("order update done at {0}".format(datetime.utcnow()))
        sleep(60*5)

@background(schedule=100)
def centraCouponsUpdate(message):
    logger.info("coupon validations started")


def demo_task():
    return None