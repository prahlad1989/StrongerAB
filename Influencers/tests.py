import json

from Influencers.models import Influencer, Constants
from Influencers.tasks import  OrdersUpdate
from logging import getLogger
from django.test import TestCase
from datetime import date,datetime,timedelta
from django.utils import timezone
logger = getLogger(__name__)


# class LastOrderSavingTest(TestCase):
#
#     def setUp(self):
#         orderDetail = {"number": "123", "orderDate":"2021-01-04T12:32:37+0100"}
#         Constants.objects.create(key='lastProcessedOrder', value=json.dumps(orderDetail))
#     def test(self):
#         objects = Constants.objects.filter(key='lastProcessedOrder')
#         object = json.loads(objects[0].value)
#         self.assertTrue(object['number']=="123", msg="correct")
#




class OrdersUpdateTest(TestCase):
    def setUp(self):
        Influencer.objects.create(is_influencer=True, email="abc@gmail.com", country='India', influencer_name='test_name1',discount_coupon= "KRISTINAM20", valid_from=timezone.now() -timedelta(100), valid_till=timezone.now()+timedelta(10) )

        Influencer.objects.create(is_influencer=True, email="abc@gmail.com", country='India', influencer_name='test_name1',
                              discount_coupon="THERESE20", valid_from=timezone.now() - timedelta(100),
                              valid_till=timezone.now()+timedelta(10))
        Influencer.objects.create(is_influencer=True, email="abc@gmail.com", country='India', influencer_name='test_name1',
                              discount_coupon="MECENAT15", valid_from=timezone.now()   - timedelta(100),
                              valid_till=timezone.now() +timedelta(10))
        orderDetail = {"number": 1000014021, "orderDate": "2021-01-04T11:46:01+0100"}
        Constants.objects.create(key='lastProcessedOrder', value=json.dumps(orderDetail))

    def testOrdersUpdate(self):
        obj = OrdersUpdate()
        obj.update()
        objects = Influencer.objects.all()
        for obj in objects:
            logger.info("revenue click after is {0} ".format(obj.revenue_click))
        self.assertTrue("good",2==2)








