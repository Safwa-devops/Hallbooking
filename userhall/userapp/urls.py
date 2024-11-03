
from django.urls import path
from . import views
urlpatterns = [
    
    path('', views.index, name="index"),
    path('new/<int:hall_id>/', views.new_booking , name="new"),
    path('about/', views.about , name="about"),
    path('contact/', views.contact , name="contact"),
    path('user_calendar/<int:hall_id>/', views.calendar_view, name='calendar'),
    path('generate_otp/', views.generate_otp , name="generate_otp"),
    path('verify_otp/', views.verify_otp , name="verify_otp"),
    path('home/', views.home, name='home'),
    path('book_hall/<int:hall_id>/', views.book_hall, name='book_hall'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('fetch_bookings/<int:hall_id>/', views.fetch_bookings, name='fetch_bookings'),
    path('check_availability/', views.check_availability, name='check_availability'),
    path('hall/<int:hall_id>/', views.hall_detail, name='hall_detail'),
    #path('hall/<int:id>/', views.hall_details, name='hall_details'),

]

