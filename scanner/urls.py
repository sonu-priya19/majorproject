# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.landing, name='landing'),              # /
#     path('home/', views.home, name='home'),               # /home/
#     path('login/', views.login_view, name='login'),
#     path('signup/', views.signup_view, name='signup'),
#     path('logout/', views.logout_view, name='logout'),
#     path('dashboard/', views.dashboard, name='dashboard'),
#     path('profile/', views.profile, name='profile'),
#     path('feedback/', views.feedback, name='feedback'),
#     path('publish-feedback/', views.publish_feedback, name='publish_feedback'),
# ]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('contact/', views.contact, name='contact'),
    path('feedback/', views.feedback, name='feedback'),
    path('publish-feedback/', views.publish_feedback, name='publish_feedback'),
    path("api/scan", views.api_scan, name="api_scan"),
    path('history/', views.history_view, name='history'),
    path("api/history", views.api_history, name="api_history"),

]