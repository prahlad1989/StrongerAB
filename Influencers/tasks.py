import json

from background_task import background
from logging import getLogger

import requests
from django.db import transaction
from django.db.models import Q, Min

from StrongerAB1.settings import centra_key, centra_api_url
from Influencers.models import Influencer as Influencer
from datetime import date, datetime, timedelta,time
from jsonpath_ng import jsonpath, parse
from django.utils import timezone
from python_graphql_client import GraphqlClient
logger = getLogger(__name__)

headers={'Authorization': 'Bearer '+str(centra_key),  'Content-Type': 'application/json' }
class CentraUpdate:
    def update(self):
        pass

class OrdersUpdate(CentraUpdate):

    def update(self):
        """Read all the influencers table in the last one month or read each row which have coupon code validation greater than today.
        pick each coupon's start date and end date.
        read all the orders in that time span , check if the order discount has that coupon. Then , update the DB.
        Read each of the """
        today = timezone.now()
        #select oldest coupon code which is still valid currently.


        filter = Q(valid_till__gte = today)
        query = Influencer.objects.filter(filter).aggregate(Min('valid_from'))
        startDate = query['valid_from__min'].date().__str__()
        influencersList = Influencer.objects.filter(filter)

        graphQlQuery = """ query  orders(where:{status: [CONFIRMED, PARTIAL, SHIPPED], orderDate: {from: $orderStartDate, to: $orderEndDate} }, limit: 5000, page: $pageNumber )
                { orderDate
                 number 
                 status 
                 grandTotal{ 
                    ...monetary }
                 discountsApplied{
                    date
                    value{value,currency{code},formattedValue}
                    ...myfrag
  }
                 
                } 
                    fragment monetary on MonetaryValue { value currency {code }}
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
                }
                    """
        client = GraphqlClient(endpoint=centra_api_url, headers=headers)
        query = {
            "query": "{orders(where: {orderDate: {from: \"2020-10-01\", to: \"endDate\"}, status: [CONFIRMED, PARTIAL, SHIPPED]},limit:5000, page: 1) {\r\n orderDate\n number\n status\n grandTotal {\n ...monetary\n }\n discountsApplied {\n date\n  ... on AppliedDiscount  {\n discount{\n id\n name\n code\n startAt\n stopAt}\n }\n }\n }  }   fragment monetary on MonetaryValue {\n value\n currency {\n code\n }\n} "}
        query["query"] = query["query"].replace("endDate", today.date().__str__())
        with transaction.atomic():
            for eachObj in influencersList:
                query["query"] = query["query"].replace("endDate", today.date().__str__())
                revenueGenerated = 0
                couponValidTill = eachObj.valid_till
                if couponValidTill >= today-timedelta(1): # will be modified later
                    coupon = eachObj.discount_coupon
                    endDate = today-timedelta(1) # correct it later
                    query["query"] = query["query"].replace("endDate", today.date().__str__())
                    resp = requests.request(method='post', url=centra_api_url, data=json.dumps(query).encode('utf-8'), headers=headers)
                    resp = (resp.content)
                    resp = json.loads(resp)
                    orders = resp['data']['orders']
                    for order in orders:
                        expr = parse('$.discountsApplied[*].discount.code')
                        values = expr.find(order)
                        values = list(map(lambda x: x.value, values))
                        logger.info("coupon codes {0}".format(values))
                        if coupon in values:
                            #logger.info("coupon {0} of influencer {1} found in order {2} so updating with price+ {3}", coupon, "created", order['number'], order['grandTotal']['value'])
                            logger.info("coupon {0} of influencer {1} found in order {2} so updating with price+ {3}".format(
                                        coupon, "created", order['number'], order['grandTotal']['value']))
                            revenueGenerated += order['grandTotal']['value']

                eachObj.revenue_click =revenueGenerated
                logger.info("revenue click generated for coupon{0} is {1}".format(coupon,revenueGenerated))
                eachObj.save()


@background(schedule=60)
def centraOrdersUpdate(message):
    logger.debug('ordersupdate started')


def demo_task():
    return None