"""StrongerAB1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from Influencers import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',views.allInfluencers,name='AllInfluencers'),
    path('index',views.index, name='login'),
    #path('logout',views.logout, name='logout'),
    # path('lead',views.Lead.as_view(),name='lead'),
    path('influencer', views.InfluencerView.as_view(), name='influencer'),
    # path('leads',login_required(views.LeadsQuery.as_view()),name='leads'),
    # path('b2b_lead',login_required(views.B2BLead.as_view()), name='b2b_lead'),
    # path('b2b_leads',login_required(views.B2BLeads.as_view()), name='b2b_leads'),
    # path('b2b_leads_query', login_required(views.B2BLeadsQuery.as_view()), name= 'b2b_leads_query'),
    # path('lead_summary',login_required(views.LeadSummary.as_view()), name ='lead_summary'),
    # path('b2b_lead_summary', login_required(views.B2BLeadSummary.as_view()), name='b2b_lead_summary'),
    path('influencers_query',login_required(views.InfluencersQuery.as_view()), name='influencers_query'),
    path('influencers', login_required(views.Influencers.as_view()), name='influencers'),
    path('all_influencers',views.allInfluencers,name='AllInfluencers'),
    path('change-password', auth_views.PasswordChangeView.as_view(success_url='all_influencers')),
    path('login', auth_views.LoginView.as_view(template_name="login.html", redirect_field_name="all_influencers")),
    path('accounts/', include('django.contrib.auth.urls')),
    path('logout', auth_views.LogoutView.as_view()),
    path('usernames',views.getUserNames,name='getUserNames'),
    path('updateCentraOrders', views.OrderUpdatesView.as_view(), name='updateCentraOrders'),
    path('updateCentraValidations', views.ValidationUpdatesView.as_view(), name='updateCentraValidations'),
    path('centraToDB', views.CentraToDB.as_view(), name= 'centraToDB'),
    path('resetCentra', views.ResetCentra.as_view(), name='resetCentra')

]
