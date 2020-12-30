from Influencers.models import Influencer
from Influencers.tasks import  OrdersUpdate
from logging import getLogger
from django.test import TestCase
from datetime import date,datetime,timedelta
from django.utils import timezone
logger = getLogger(__name__)

class OrdersUpdateTest(TestCase):
    def setUp(self):
        Influencer.objects.create(is_influencer=True, email="abc@gmail.com", country='India', influencer_name='test_name1',discount_coupon= "MECENAT15", valid_from=timezone.now() -timedelta(100), valid_till=timezone.now() )

        Influencer.objects.create(is_influencer=True, email="abc@gmail.com", country='India', influencer_name='test_name1',
                              discount_coupon="THERESE20", valid_from=timezone.now() - timedelta(100),
                              valid_till=timezone.now()+timedelta(10))
        Influencer.objects.create(is_influencer=True, email="abc@gmail.com", country='India', influencer_name='test_name1',
                              discount_coupon="20DANIFIT", valid_from=timezone.now()   - timedelta(100),
                              valid_till=timezone.now() +timedelta(10))

    def testOrdersUpdate(self):
        obj = OrdersUpdate()
        obj.update()
        print("stupid")
        objects = Influencer.objects.all()
        for obj in objects:
            logger.info("revenue click after is {0} ".format(obj.revenue_click))
        self.assertTrue("good",2==2)








