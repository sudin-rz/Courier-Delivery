from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from main import views

from main.customer import views as customer_views
from main.courier import views as courier_views,apis as courier_apis

customer_urlpatterns=[
    path('',customer_views.home, name='home'),
    path('profile/',customer_views.profile_page,name="profile"),
    path('payment_method/',customer_views.payment_method_page,name="payment_method"),
    path('create_job/',customer_views.create_job_page,name="create_job"),

    path('jobs/current/',customer_views.current_jobs_page,name="current_jobs"),
    path('jobs/archived/',customer_views.archived_jobs_page,name="archived_jobs"),
    path('jobs/<job_id>/',customer_views.job_page,name="job"),
    
]

courier_urlpatterns=[
    path('',courier_views.home, name="home"),
    path('jobs/available/',courier_views.available_jobs_page, name="available_jobs"),

    path('api/jobs/available/',courier_apis.available_jobs_api, name="available_jobs_api"),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),


    path('sign_in/', auth_views.LoginView.as_view(template_name="sign_in.html"), name='sign_in'),

    path('sign_out/', auth_views.LogoutView.as_view(next_page="/"), name='sign_out'),
    path('sign_up/', views.sign_up, name='sign_up'),
    
    path('customer/', include((customer_urlpatterns,'customer'))),
    path('courier/',  include((courier_urlpatterns,'courier'))),


    # Include allauth URLs for authentication
    path('accounts/', include('allauth.urls')),


    # URL pattern for Google login
    path('login/google/', views.google_login, name='google_login'),

    path('login/google/callback/', views.google_callback, name='google_callback'),


    # path('', include('social_django.urls')),


    # Include social authentication URLs

    path('', include('social_django.urls', namespace='social')),    

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

