from django.shortcuts import render, redirect, get_object_or_404
from django.http import *
from django.db.models.fields.files import ImageField
from django.urls import reverse
from django.http import JsonResponse
from django.core import serializers
import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import *
from django.contrib import messages
from django.utils import timezone
import logging
import json
from django.core.cache import cache
from datetime import datetime, timedelta
from django.core.files.storage import FileSystemStorage
from adminhall.adminapp.models import *
from django.db.models import Q

def index(request):
    halls_with_images = []
    all_slideshow_images = []  # To hold all images for the slideshow

    halls = Hall.objects.filter(isdelete = 0)
    hall_locations = Hall.objects.values_list('place', flat=True).distinct()
    print(f"Number of halls fetched: {halls.count()}")

    for hall in halls:
        # Get all images for the hall
        all_images = Imagegallery.objects.filter(hall=hall)
        image_urls = [image.image.url for image in all_images]
        
        # Get the first image for thumbnail
        thumbnail_url = image_urls[0] if image_urls else None

        # Append hall data with images to the list
        halls_with_images.append({
            'hall': hall,
            'thumbnail': thumbnail_url,  # First image for thumbnail
            'images': image_urls,  # All images for slideshow
        })

        # Add all images to the slideshow list
        all_slideshow_images.extend(image_urls)

    context = {
        'halls_with_images': halls_with_images,  # Pass hall and thumbnail details to the context
        'all_slideshow_images': all_slideshow_images,  # Pass all images to the context
        'hall_locations': hall_locations,
    }

    print(context)

    return render(request, 'user_index.html',context)


def new_booking(request, hall_id):
    hall = get_object_or_404(Hall, id=hall_id)
    
    # Fetch available feature IDs for the selected hall
    hall_feature_ids = Hallfeature.objects.filter(hall=hall, isdelete=0).values_list('feature', flat=True)
    
    # Fetch feature names based on the IDs
    hall_features = Feature.objects.filter(id__in=hall_feature_ids, isdelete=0)
    ac_type = hall.ac_nonac_both
    # Fetch terms and conditions from the hall
    terms = hall.terms  # Assuming 'terms' is a field in your Hall model

    if request.method == 'POST':
        date = request.POST.get('date')
        timeslot = request.POST.get('timeslot')
        
        print(date)
        print(timeslot)
        print(hall_id)
        print(hall)
        previous_date = (timezone.datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).date()
        print(previous_date)
        is_evening_available = check_evening_availability(hall_id, previous_date)
        # Render the form with these default values pre-filled
        return render(request, 'new_booking.html', {
            'hall_id': hall_id,
            'hall_name': hall.name,
            'selected_date': date,
            'selected_timeslot': timeslot,
            'hall_features': hall_features,  # Pass feature names to the template
            'terms': terms,  # Pass terms to the template
            'ac_type':ac_type,
            'is_evening_available': is_evening_available,
        })

    # On GET request, render the form without pre-filled values
    return render(request, 'new_booking.html', {
        'hall_id': hall_id,
        'hall_features': hall_features,  # Pass feature names to the template
        'terms': terms,  # Pass terms to the template
    })


def check_evening_availability(hall_id, date):
    # Convert date string to a datetime object if needed
    # If date is a string, convert it first. Otherwise, skip this step.
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d").date()

    # Get the day of the week (0=Monday, 6=Sunday)
    day_of_week = date.weekday()  # Monday is 0, Sunday is 6
    
    # print(date)
    # print(hall_id)
    
    
    is_booked = Booking.objects.filter(
        hall_id=hall_id,
        date=date
    ).filter(
        Q(timeslot="Evening") | Q(timeslot="Full Day")
    ).exists()
    
    # print(is_booked)
    
    
    is_inoperable = Inoperability.objects.filter(
        hall_id=hall_id,
        start_date__lte=date,
        end_date__gte=date
    ).exists()

    # Check for availability based on the day of the week
    availability = Availability.objects.filter(hall_id=hall_id).first()
    is_unavailable = False
    if availability:
        # Check the specific day of the week based on the weekday
        if day_of_week == 0:  # Monday
            is_unavailable = availability.monday == 0
        elif day_of_week == 1:  # Tuesday
            is_unavailable = availability.tuesday == 0
        elif day_of_week == 2:  # Wednesday
            is_unavailable = availability.wednesday == 0
        elif day_of_week == 3:  # Thursday
            is_unavailable = availability.thursday == 0
        elif day_of_week == 4:  # Friday
            is_unavailable = availability.friday == 0
        elif day_of_week == 5:  # Saturday
            is_unavailable = availability.saturday == 0
        elif day_of_week == 6:  # Sunday
            is_unavailable = availability.sunday == 0

    print(is_booked)
    print(is_inoperable)
    print(is_unavailable)
    return not (is_booked or is_inoperable or is_unavailable)



def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def home(request):
    return render(request, 'hallbooking_app/home.html')

def calendar_view(request,hall_id):
    print(hall_id)
    return render(request, 'user_calendar.html' , {'hall_id' : hall_id} )




# def book_hall(request, hall_id=None):
#     if request.method == 'POST':
#         # Temporarily disable OTP check
#         # if not request.session.get('otp_verified', False):
#         #     return JsonResponse({'success': False, 'message': 'OTP verification required'}, status=400)

#         # Extract form data without validation
#         name = request.POST.get('name')
#         number = request.POST.get('number')
#         address = request.POST.get('address')
#         startDate = request.POST.get('start_date')
#         event_type = request.POST.get('event_type')
#         event_details = request.POST.get('specify') if event_type == 'others' else None
#         event_description = request.POST.get('event_description')
#         timeslot = request.POST.get('timeslot')
#         selected_ac = request.POST.get('selected_ac', 1)  # Defaults to 1 if not provided
#         evening_before = request.POST.get('eveningBefore')
#         features = request.POST.getlist('features')
#         otp_value = request.POST.get('otp')  # Keep in place, but no validation
#         email = request.session.get('email')

#         # Temporarily disable required fields check
#         # if not all([name, number, address, startDate, timeslot]):
#         #     return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)

#         # Get the hall
#         selected_hall = get_object_or_404(Hall, id=hall_id)

#         # Create user contact details
#         user_contact = User.objects.create(
#             name=name, number=number, email=email, address=address
#         )

#         # Create OTP record for the user (optional to remove this)
#         User_OTP.objects.create(
#             otp=otp_value,
#             is_verified=False,
#             user=user_contact
#         )

#         # Create the primary booking
#         booking = Booking.objects.create(
#             date=startDate,
#             user=user_contact,
#             event_name=event_type if event_type != 'others' else event_details,
#             description=event_description,
#             approval_status=0,
#             ac=selected_ac,
#             timeslot=timeslot,
#             evening_before=evening_before,
#             features=', '.join(features),
#             hall=selected_hall,
#         )

#         # Handle "full day" booking (optional - can comment out this part)
#         if timeslot == "Full Day":
#             date = datetime.strptime(startDate, "%Y-%m-%d")
#             day_before = (date - timedelta(days=1)).date()

#             Booking.objects.create(
#                 date=day_before,
#                 user=user_contact,
#                 event_name=event_type if event_type != 'others' else event_details,
#                 description=event_description,
#                 approval_status=0,
#                 ac=selected_ac,
#                 timeslot="Evening",
#                 evening_before="no",
#                 features=', '.join(features),
#                 hall=selected_hall,
#             )

#         # Redirect after successful booking
#         new_booking_url = reverse('book_hall', kwargs={'hall_id': hall_id})
#         print("happy")
#         return redirect(f'{new_booking_url}?success=true')


# def book_hall(request, hall_id=None):
#     if request.method == 'POST':
#         try:
#             # Extract form data without validation
#             name = request.POST.get('name')
#             number = request.POST.get('number')
#             address = request.POST.get('address')
#             startDate = request.POST.get('start_date')
#             event_type = request.POST.get('event_type')
#             event_details = request.POST.get('specify') if event_type == 'others' else None
#             event_description = request.POST.get('event_description')
#             timeslot = request.POST.get('timeslot')
#             selected_ac = request.POST.get('selected_ac', 1)  # Defaults to 1 if not provided
#             evening_before = request.POST.get('eveningBefore')
#             features = request.POST.getlist('features')
#             email = request.session.get('email')
#             otp_value = request.POST.get('otp')

#             # Get the hall
#             selected_hall = get_object_or_404(Hall, id=hall_id)

#             # Create user contact details
#             user_contact = User.objects.create(
#                 name=name, number=number, email=email, address=address
#             )

#             user_otp = User_OTP.objects.create(
#                 otp=otp_value,
#                 is_verified=False,  # Assuming OTP is not verified right now
#                 user=user_contact
#             )
#             # Create the primary booking
#             booking = Booking.objects.create(
#                 date=startDate,
#                 user=user_contact,
#                 event_name=event_type if event_type != 'others' else event_details,
#                 description=event_description,
#                 approval_status=0,
#                 ac=selected_ac,
#                 timeslot=timeslot,
#                 evening_before=evening_before,
#                 features=', '.join(features),
#                 hall=selected_hall,
#             )

#             # Handle "full day" booking (optional)
#             if timeslot == "Full Day":
#                 date = datetime.strptime(startDate, "%Y-%m-%d")
#                 day_before = (date - timedelta(days=1)).date()

#                 Booking.objects.create(
#                     date=day_before,
#                     user=user_contact,
#                     event_name=event_type if event_type != 'others' else event_details,
#                     description=event_description,
#                     approval_status=0,
#                     ac=selected_ac,
#                     timeslot="Evening",
#                     evening_before="no",
#                     features=', '.join(features),
#                     hall=selected_hall,
#                 )

#             # Redirect after successful booking
#             return JsonResponse({'success': True, 'message': 'Hall booked successfully'})

#         except Exception as e:
#             return JsonResponse({'success': False, 'message': str(e)}, status=400)

#     return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


def book_hall(request, hall_id=None):
    if request.method == 'POST':
        try:
            # Extract form data without validation
            name = request.POST.get('name')
            number = request.POST.get('number')
            address = request.POST.get('address')
            startDate = request.POST.get('start_date')
            event_type = request.POST.get('event_type')
            event_details = request.POST.get('specify') if event_type == 'others' else None
            event_description = request.POST.get('event_description')
            timeslot = request.POST.get('timeslot')
            selected_ac = request.POST.get('selected_ac', 1)  # Defaults to 1 if not provided
            evening_before = request.POST.get('eveningBefore')
            features = request.POST.getlist('features')
            email = request.session.get('email')
            otp_value = request.POST.get('otp')

            # Get the hall
            selected_hall = get_object_or_404(Hall, id=hall_id)

            # Create user contact details
            user_contact = User.objects.create(
                name=name, number=number, email=email, address=address
            )

            # Fetch the last created User_OTP object and update the user field
            user_otp = User_OTP.objects.latest('id')
            user_otp.user = user_contact
            user_otp.save()

            # Create the primary booking
            booking = Booking.objects.create(
                date=startDate,
                user=user_contact,
                event_name=event_type if event_type != 'others' else event_details,
                description=event_description,
                approval_status=0,
                ac=selected_ac,
                timeslot=timeslot,
                evening_before=evening_before,
                features=', '.join(features),
                hall=selected_hall,
            )

            # Handle "full day" booking (optional)
            if timeslot == "Full Day":
                date = datetime.strptime(startDate, "%Y-%m-%d")
                day_before = (date - timedelta(days=1)).date()

                Booking.objects.create(
                    date=day_before,
                    user=user_contact,
                    event_name=event_type if event_type != 'others' else event_details,
                    description=event_description,
                    approval_status=0,
                    ac=selected_ac,
                    timeslot="Evening",
                    evening_before="no",
                    features=', '.join(features),
                    hall=selected_hall,
                )

            # Redirect after successful booking
            return JsonResponse({'success': True, 'message': 'Hall booked successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


def fetch_bookings(request, hall_id):
    bookings = Booking.objects.filter(hall_id=hall_id).values('date', 'timeslot')
    inoperable = Inoperability.objects.filter(hall_id=hall_id).values('start_date','end_date')
    availability = Availability.objects.filter(hall_id=hall_id).values('sunday','monday','tuesday','wednesday','thursday','friday','saturday')
    response_data = {
        'bookings': list(bookings),
        'inoperable': list(inoperable),
        'availability': list(availability),
    }
    print(response_data)
    # Return the combined data as a JSON response
    return JsonResponse(response_data, safe=False)

def generate_otp():
    """Generate a 6-digit OTP"""
    return random.randint(100000, 999999)

def check_availability(request):
    date = request.GET.get('date')
    timeslot = request.GET.get('timeslot')
    hall_id = request.GET.get('hall_id')
    
    is_available = not Booking.objects.filter(hall_id=hall_id, date=date, timeslot=timeslot).exists()
    return JsonResponse({'available': is_available})


def hall_detail(request, hall_id):
    # Fetch the hall by its ID
    hall = get_object_or_404(Hall, id=hall_id)

    # Get all images related to the hall
    images = Imagegallery.objects.filter(hall=hall)

    # Get all features related to the hall (via HallFeature model)
    hall_features = Hallfeature.objects.filter(hall=hall)
    features = [hall_feature.feature for hall_feature in hall_features]

    # Get the corresponding Feature objects
    features = Feature.objects.filter(id__in=features)
    feature_names = [feature.featurename for feature in features]  # Extract feature names

    # Prepare rent information based on AC and non-AC types
    rent_info = {}
    print(hall.ac_nonac_both)
    if hall.ac_nonac_both == 'A/C':
        rent_info['type'] = 'A/C'
        rent_info['rent'] = hall.ac_rent
        print(rent_info)
    elif hall.ac_nonac_both == 'Non A/C':
        rent_info['type'] = 'Non A/C'
        rent_info['rent'] = hall.non_ac_rent
        print(rent_info)
    elif hall.ac_nonac_both == 'Both A/C and Non A/C':
        rent_info['type'] = 'Both A/C and Non A/C'
        rent_info['ac_rent'] = hall.ac_rent
        rent_info['non_ac_rent'] = hall.non_ac_rent
        print(rent_info)
    print(rent_info)
    context = {
        'hall': hall,
        'images': images,  
        'features': features,
        'rent_info': rent_info,  # Add rent information to context
    }
    
    return render(request, 'hall_detail.html', context)





def send_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        
        # Generate OTP
        otp = generate_otp()  # Make sure this function is implemented
        
        # Store OTP and email in session
        request.session['otp'] = otp
        request.session['email'] = email
        
        # You can print the OTP for testing purposes
        print(f"Generated OTP: {otp}")
        
        print("otp sent successfully")
        user_otp = User_OTP.objects.create(
                otp=otp,
                is_verified=False,  # Assuming OTP is not verified right now
            )
        print(user_otp)
        return JsonResponse({'success': True, 'message': 'OTP sent successfully'})

    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


# def verify_otp(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         entered_otp = data.get('otp')
        
#         # Retrieve OTP and email from session
#         session_otp = str(request.session.get('otp'))
#         email = request.session.get('email')
        
      
#         if entered_otp == session_otp:
#             # Mark OTP as verified in the session
#             request.session['otp_verified'] = True
#             print("otp verified successfully")
#             return JsonResponse({'success': True, 'message': 'OTP verified successfully'})
#         else:
#             print("wrong otp")
#             return JsonResponse({'success': False, 'message': [entered_otp,session_otp] })
#     return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


def verify_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        entered_otp = data.get('otp')
        
        # Retrieve OTP and email from session
        session_otp = str(request.session.get('otp'))
        email = request.session.get('email')

        if entered_otp == session_otp:
            # Mark OTP as verified in the session
            request.session['otp_verified'] = True
            
            # Fetch the last created User_OTP object and update is_verified
            user_otp = User_OTP.objects.latest('id')
            user_otp.is_verified = True
            user_otp.save()

            print("OTP verified and updated successfully.")
            return JsonResponse({'success': True, 'message': 'OTP verified successfully'})
        else:
            print("Wrong OTP")
            return JsonResponse({'success': False, 'message': [entered_otp, session_otp] })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
