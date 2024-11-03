from django.shortcuts import render,redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import *
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils import timezone
import calendar
from datetime import datetime, timedelta
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.template.loader import render_to_string

def adminregister(request):
    if request.method == "POST":
        username= request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
         # Check if superadmin checkbox is checked
        superadmin = 1 if request.POST.get('superadmin') else 0
        reg=Adminrecord.objects.create(
            username=username,
            password=password,
            email=email,
            superadmin=superadmin,
            )
    return render(request,'register.html')

def adminlogin(request):
    message = None  # Initialize the message variable to avoid UnboundLocalError

    try:
        if request.method == "POST":
            Booked_list=Booking.objects.all()
            username = request.POST.get('username')
            password = request.POST.get('password')

            # Authenticate user
            if Adminrecord.objects.filter(username=username, password=password).exists():
                user = Adminrecord.objects.get(username=username, password=password)
                super_admin=Adminrecord.objects.filter(superadmin=1)
                is_super_admin = user.superadmin == 1 #check login user superadmin or not
                request.session['uid'] = user.id
                return render(request,'booklist.html',{'Booked_list':Booked_list,'is_super_admin':is_super_admin}) 
            else:
                message = "Invalid username or password"  # Set message for invalid credentials
    except Exception as e:
        return HttpResponse(f'An error occurred: {e}')

    return render(request, 'login.html', {'message': message})  # Pass the message to the template

def member(request):
    # Get admins that are not superadmin and not marked as deleted
    admin = Adminrecord.objects.exclude(superadmin=1).exclude(isdelete=1)
    return render(request, 'member_list.html', {'admin': admin})

def delete_member(request, admin_id):
    admin_to_delete = get_object_or_404(Adminrecord, id=admin_id)
    # Mark as deleted instead of actually deleting the record
    admin_to_delete.isdelete = 1
    admin_to_delete.save()  # Save the changes to the database
    return redirect('member')

def hallmanage(request):
    if request.method == "POST":
        print("Received POST request")
        # Collect hall details from the form
        hall = request.POST.get('name')
        description= request.POST.get('description')
        place = request.POST.get('place')
        landmark = request.POST.get('landmark')
        location = request.POST.get('location')
        pincode = request.POST.get('pincode')
        district = request.POST.get('district')
        capacity = request.POST.get('capacity')
        actype = request.POST.get('actype')
        ac_rent = request.POST.get('ac_rent')
        non_ac_rent = request.POST.get('non_ac_rent')
        owner = request.POST.get('owner')
        contact = request.POST.get('contact')
        availability = request.POST.getlist('availability')
        features = request.POST.getlist('feature')
        terms= request.POST.get('terms')
        # Handle multiple image uploads
        images = request.FILES.getlist('image')  # Get list of uploaded images
        print(images)
        print("Uploaded images:", [image.name for image in images])  # Print uploaded image names

        # Create the Hall instance
        hall_save = Hall.objects.create(
            name=hall,
            description=description,
            place=place,
            landmark=landmark,
            location=location,
            pincode=pincode,
            district=district,
            capacity=capacity,
            ac_nonac_both=actype,
            ac_rent=ac_rent,
            non_ac_rent=non_ac_rent,
            owner_name=owner,
            contact=contact,
            availability=availability,
            # feature=features,
            terms=terms,
        )
        print(hall_save)
          # Save images to the Imagegallery table
        if images:
            for myfile in images:
                Imagegallery.objects.create(hall=hall_save, image=myfile)
            messages.success(request, f"{len(images)} images uploaded successfully!")
        else:
            messages.warning(request, "No images were uploaded.")

        # Save features
        for feat in features:
            Hallfeature.objects.create(
                hall=hall_save,
                feature=feat
        )


        # Process availability checkboxes
        availability_dict = {
            'sunday': 1 if 'Sun' in availability else 0,
            'monday': 1 if 'Mon' in availability else 0,
            'tuesday': 1 if 'Tue' in availability else 0,
            'wednesday': 1 if 'Wed' in availability else 0,
            'thursday': 1 if 'Thu' in availability else 0,
            'friday': 1 if 'Fri' in availability else 0,
            'saturday': 1 if 'Sat' in availability else 0,
        }
        Availability.objects.create(
            hall=hall_save,
            sunday=availability_dict['sunday'],
            monday=availability_dict['monday'],
            tuesday=availability_dict['tuesday'],
            wednesday=availability_dict['wednesday'],
            thursday=availability_dict['thursday'],
            friday=availability_dict['friday'],
            saturday=availability_dict['saturday'],
        )

        # Check total images saved
        total_images = Imagegallery.objects.filter(hall=hall_save).count()
        print(f"Total images for hall {hall_save.id}: {total_images}")

    feature_display = Feature.objects.exclude(isdelete=1)
    return render(request, 'hall.html', {'feature_display': feature_display})

def viewhall(request):
    hall_view=Hall.objects.exclude(isdelete=1)
    return render(request,'hallview.html',{'hall_view':hall_view})

def hall_detail(request, id):
    hallview = get_object_or_404(Hall, id=id)
    # Adjusted image retrieval to get all images related to the hall
    images = Imagegallery.objects.filter(hall=hallview)
    hall_features = Hallfeature.objects.filter(hall=id)
    features = [hall_feature.feature for hall_feature in hall_features]
    
    # Get the corresponding Feature objects
    features = Feature.objects.filter(id__in=features)
    feature_names = [feature.featurename for feature in features]  # Extract feature names
    
    return render(request, 'hall_view_detail.html', {
        'view': hallview,
        'images': images,  # Pass the list of images
        'features': feature_names
    })

def delete_hall(request, id):
    delete_hall = get_object_or_404(Hall, id=id)
    delete_hall.isdelete = 1
    delete_hall.delete()
    delete_hall.save()
    return HttpResponseRedirect(reverse(viewhall))

# def updatehall(request, id):
#     hall_update = get_object_or_404(Hall, id=id)
#     # hall_feature= get_object_or_404(Hallfeature, id=id)

#     if request.method == "POST":
#         # Collect hall details from the form
#         hall_update.name = request.POST.get('name')
#         hall_update.description = request.POST.get('description')
#         hall_update.place = request.POST.get('place')
#         hall_update.landmark = request.POST.get('landmark')
#         hall_update.pincode = request.POST.get('pincode')
#         hall_update.district = request.POST.get('district')
#         hall_update.capacity = request.POST.get('capacity')
#         hall_update.ac_nonac_both = request.POST.get('actype')
#         hall_update.ac_rent = request.POST.get('ac_rent')
#         hall_update.non_ac_rent = request.POST.get('non_ac_rent')
#         hall_update.owner_name = request.POST.get('owner')
#         hall_update.contact = request.POST.get('contact')
#         hall_update.save()     

#         if request.method == "POST": # Handle feature updates
#             selected_features = request.POST.getlist('feature')
#             Hallfeature.objects.filter(hall=hall_update).delete() # Clear existing features
#             for feature_id in selected_features:
#                 Hallfeature.objects.create(hall=hall_update, feature=feature_id)

#         messages.success(request, "Hall updated successfully!")
#         return redirect('updatehall', id=id)
       
#     feature_display = Feature.objects.exclude(isdelete=1)
#     for feat in feature_display:
#         print(feat)
#     # selected_features = list(Hallfeature.objects.filter(hall=hall_update).values_list('feature', flat=True))  # Get current feature values
    
#     selected_features = list(Hallfeature.objects.filter(hall=hall_update).values_list('feature', flat=True))
#     selected_features = list(map(int, selected_features))  # Convert to integers
    
#      # Update availability
#     availability = request.POST.getlist('availability')
#     Availability.objects.update_or_create(
#         hall=hall_update,
#         defaults={
#             'sunday': 1 if 'Sun' in availability else 0,
#             'monday': 1 if 'Mon' in availability else 0,
#             'tuesday': 1 if 'Tue' in availability else 0,
#             'wednesday': 1 if 'Wed' in availability else 0,
#             'thursday': 1 if 'Thu' in availability else 0,
#             'friday': 1 if 'Fri' in availability else 0,
#             'saturday': 1 if 'Sat' in availability else 0,
#         }
#     )

#     availability_instance = Availability.objects.filter(hall=hall_update).first()
#     return render(request, 'hall_update.html', {'hall_update': hall_update, 'feature_display': feature_display,'selected_features': selected_features, 'availability':availability_instance })
    

def updatehall(request, id):
    hall_update = get_object_or_404(Hall, id=id)

    if request.method == "POST":
        # Collect hall details from the form
        hall_update.name = request.POST.get('name')
        hall_update.description = request.POST.get('description')
        hall_update.place = request.POST.get('place')
        hall_update.landmark = request.POST.get('landmark')
        hall_update.location = request.POST.get('location')
        hall_update.pincode = request.POST.get('pincode')
        hall_update.district = request.POST.get('district')
        hall_update.capacity = request.POST.get('capacity')
        hall_update.ac_nonac_both = request.POST.get('actype')
        hall_update.ac_rent = request.POST.get('ac_rent')
        hall_update.non_ac_rent = request.POST.get('non_ac_rent')
        hall_update.owner_name = request.POST.get('owner')
        hall_update.contact = request.POST.get('contact')
        hall_update.save()     

        # Handle feature updates
        selected_features = request.POST.getlist('feature')
        Hallfeature.objects.filter(hall=hall_update).delete()  # Clear existing features
        for feature_id in selected_features:
            Hallfeature.objects.create(hall=hall_update, feature=feature_id)

        # Handle image updates
        if 'images' in request.FILES:
            for image in request.FILES.getlist('images'):
                Imagegallery.objects.create(hall=hall_update, image=image)

        # Handle image deletions
        if 'delete_images' in request.POST:
            images_to_delete = request.POST.getlist('delete_images')
            Imagegallery.objects.filter(id__in=images_to_delete).delete()

        # Update availability
        availability = request.POST.getlist('availability')
        Availability.objects.update_or_create(
            hall=hall_update,
            defaults={
                'sunday': 1 if 'Sun' in availability else 0,
                'monday': 1 if 'Mon' in availability else 0,
                'tuesday': 1 if 'Tue' in availability else 0,
                'wednesday': 1 if 'Wed' in availability else 0,
                'thursday': 1 if 'Thu' in availability else 0,
                'friday': 1 if 'Fri' in availability else 0,
                'saturday': 1 if 'Sat' in availability else 0,
            }
        )

        messages.success(request, "Hall updated successfully!")
        return redirect('updatehall', id=id)
    
    feature_display = Feature.objects.exclude(isdelete=1)
    selected_features = list(Hallfeature.objects.filter(hall=hall_update).values_list('feature', flat=True))
    selected_features = list(map(int, selected_features))  # Convert to integers
    
    # Fetch existing images
    existing_images = Imagegallery.objects.filter(hall=hall_update, isdelete=0)

    availability_instance = Availability.objects.filter(hall=hall_update).first()
    return render(request, 'hall_update.html', {
        'hall_update': hall_update,
        'feature_display': feature_display,
        'selected_features': selected_features,
        'availability': availability_instance,
        'existing_images': existing_images,
    })
   


def upcoming(request):
    today = timezone.now().date()
    upcoming = Booking.objects.filter(approval_status=1,date__gte=today)
    return render(request, 'upcoming_event.html', {'upcoming': upcoming})

def history(request):
    today = timezone.now().date()
    history= Booking.objects.filter(approval_status=1,date__lte=today)
    return render(request, 'booking_history.html', {'history': history})

from django.shortcuts import render, get_object_or_404
from .models import Booking, Hall
from django.utils import timezone
from datetime import timedelta



# def report(request):
#     all_halls = Hall.objects.exclude(isdelete=1)  # Get all active halls
#     filtered_bookings = Booking.objects.select_related('hall')

#     hall_filter = request.GET.get('hall')
#     date_filter = request.GET.get('date_filter')

#     # Apply hall filtering
#     if hall_filter:
#         filtered_bookings = filtered_bookings.filter(hall__id=hall_filter)

#     # Apply date filtering
#     if date_filter:
#         today = timezone.now().date()
#         if date_filter == 'day':
#             start_date = today
#             end_date = today + timedelta(days=1)
#         elif date_filter == 'week':
#             start_date = today - timedelta(days=today.weekday())
#             end_date = start_date + timedelta(weeks=1)
#         elif date_filter == 'month':
#             start_date = today.replace(day=1)
#             end_date = (start_date + timedelta(days=31)).replace(day=1)
#         elif date_filter == 'year':
#             start_date = today.replace(month=1, day=1)
#             end_date = today.replace(month=1, day=1, year=today.year + 1)
#         else:
#             start_date = None
#             end_date = None

#         if start_date and end_date:
#             filtered_bookings = filtered_bookings.filter(date__gte=start_date, date__lt=end_date)

#     context = {
#         'bookings': filtered_bookings,
#         'all_halls': all_halls,
#         'selected_hall': hall_filter,
#         'selected_date_filter': date_filter,
#     }
#     return render(request, 'hallreport.html', context)

def report(request):
    all_halls = Hall.objects.exclude(isdelete=1)
    filtered_bookings = Booking.objects.select_related('hall')

    hall_filter = request.GET.get('hall')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    timeslot_filter = request.GET.get('timeslot')

    # Apply hall filtering
    if hall_filter:
        filtered_bookings = filtered_bookings.filter(hall__id=hall_filter)

    # Apply date range filtering
    if start_date and end_date:
        filtered_bookings = filtered_bookings.filter(date__gte=start_date, date__lte=end_date)

    # Apply timeslot filtering
    if timeslot_filter:
        filtered_bookings = filtered_bookings.filter(timeslot=timeslot_filter)

    context = {
        'bookings': filtered_bookings,
        'all_halls': all_halls,
        'selected_hall': hall_filter,
        'start_date': start_date,
        'end_date': end_date,
        'selected_timeslot': timeslot_filter,
    }
    return render(request, 'hallreport.html', context)

# def generate_pdf(request):
#     bookings = Booking.objects.exclude(isdelete=1).select_related('hall')
#     # Get the filtering options from the request
#     hall_filter = request.GET.get('hall')
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')
#     timeslot_filter = request.GET.get('timeslot')

#     if hall_filter:
#         bookings = bookings.filter(hall__id=hall_filter)
#     if start_date and end_date:
#         bookings = bookings.filter(date__gte=start_date, date__lte=end_date)
#     if timeslot_filter:
#         bookings = bookings.filter(timeslot=timeslot_filter)

#     # Generate PDF
#     html_string = render_to_string('pdf_template.html', {'bookings': bookings})
#     html = HTML(string=html_string)
    
#     pdf_path = f"media/reports/bookings_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
#     html.write_pdf(pdf_path)

#     # Serve the PDF file
#     response = HttpResponse(open(pdf_path, 'rb').read(), content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
#     return response


def generate_pdf(request):

    # Create the response object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="booking_report.pdf"'
    
    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter  # Get the width and height of the page

    # Add a title to the PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Booking Report")

    # Set font for the details
    p.setFont("Helvetica", 12)

    # Fetch all bookings from the database
    bookings = Booking.objects.all()  # You can add filters based on request parameters

    # Set initial position for the first entry
    y_position = height - 100

    # Iterate through bookings and add them to the PDF
    for booking in bookings:
        # Customize the details to be displayed
        booking_details = f"Hall: {booking.hall.name}, Date: {booking.date}, Time: {booking.timeslot}, Reason: {booking.event_name}"
        p.drawString(100, y_position, booking_details)
        y_position -= 20  # Move down for the next entry

        # Check if we need to create a new page
        if y_position < 50:
            p.showPage()
            p.setFont("Helvetica", 12)
            y_position = height - 100

    # Finalize the PDF
    p.showPage()
    p.save()
    
    return response

def generate_report(request):
    # bookings = []  # Initialize an empty list for bookings
    
    # if request.method == 'POST':
    #     hall = request.POST.get('hall')
    #     date = request.POST.get('date')
    #     report_type = request.POST.get('report_type')

    #     # Convert date to a usable format
    #     if date:
    #         date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        
    #     # Fetch data based on hall, date, and report type
    #     if report_type == 'upcoming':
    #         bookings = Booking.objects.filter(hall=hall, date__gte=date)
    #     elif report_type == 'past':
    #         bookings = Booking.objects.filter(hall=hall, date__lt=date)
    #     else:
    #         bookings = Booking.objects.filter(hall=hall)

    #     # Render the PDF template with the fetched data
    #     html_string = render_to_string('report_template.html', {'bookings': bookings})
    #     pdf = HTML(string=html_string).write_pdf()

    #     # Create a response with the PDF
    #     response = HttpResponse(pdf, content_type='application/pdf')
    #     response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    #     return response
    
    return render(request, 'report_form.html')

def generate_pdf_report(request):
    # Create the response object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="booking_report.pdf"'
    
    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter  # Get the width and height of the page

    # Add a title to the PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Booking Report")

    # Set font for the details
    p.setFont("Helvetica", 12)

    # Fetch all bookings from the database
    bookings = Booking.objects.all()  # You can add filters based on request parameters

    # Set initial position for the first entry
    y_position = height - 100

    # Iterate through bookings and add them to the PDF
    for booking in bookings:
        # Customize the details to be displayed
        booking_details = f"Hall: {booking.hall.name}, Date: {booking.date}, Time: {booking.time_slot}, Reason: {booking.reason}"
        p.drawString(100, y_position, booking_details)
        y_position -= 20  # Move down for the next entry

        # Check if we need to create a new page
        if y_position < 50:
            p.showPage()
            p.setFont("Helvetica", 12)
            y_position = height - 100

    # Finalize the PDF
    p.showPage()
    p.save()
    

def print_booking(request, id):
    booking = get_object_or_404(Booking, id=id)

    # Create the response object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="booking_{booking.id}.pdf"'

    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter  # Get the width and height of the page

    # Add a title to the PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Booking Details")

    # Set font for the details
    p.setFont("Helvetica", 12)

    # Add booking details
    details = [
        f"User Name: {booking.user.name}",
        f"Hall Name: {booking.hall.name}",
        f"Date: {booking.date}",
        f"Timeslot: {booking.timeslot}",
        f"Reason: {booking.event_name}"
    ]

    # Set initial position for details
    y_position = height - 100

    for detail in details:
        p.drawString(100, y_position, detail)
        y_position -= 20  # Move down for the next detail

    # Finalize the PDF
    p.showPage()
    p.save()

    return response


def featuremanage(request):
    all_feature=Feature.objects.exclude(isdelete=1)
    update_feature=None
    if request.method=='POST':
        feature=request.POST.get('featurename')
        feature_id=request.POST.get('feature_id')
        if feature_id:
            try:
                update_feature=Feature.objects.get(id=feature_id)
                update_feature.featurename=feature
                update_feature.save()
            except Feature.DoesNotExist:
                pass
        else:
            update_feature=Feature(featurename=feature)
            update_feature.save()
        return redirect(featuremanage)
    return render(request,'hallfeature.html',{'allfeature':all_feature,'updatefeature':update_feature})

def update_feature(request, id): 
    try:
        update_feature = Feature.objects.get(id=id)
        return render(request, 'hallfeature.html',{
            'updatefeature': update_feature,
            'allfeature': Feature.objects.exclude(isdelete=1),
        })
    except Feature.DoesNotExist:
        return HttpResponseRedirect(reverse('featuremanage'))
    
def delete_feature(request, id):
    delete_feature = get_object_or_404(Feature, id=id)
    delete_feature.isdelete = 1
    delete_feature.delete()
    delete_feature.save()
    return HttpResponseRedirect(reverse('featuremanage'))


def hallinoperabilitymanage(request):
    all_hall = Hall.objects.exclude(isdelete=1)
    all_inoperability = Inoperability.objects.exclude(isdelete=1).select_related('hall')
    update_inoperability = None

    if request.method == "POST":
        inoperability_id = request.POST.get('inoperability_id')
        hall_id = request.POST.get('hall')
        hall_obj = get_object_or_404(Hall, id=hall_id)
        start = request.POST.get('startdate')
        end = request.POST.get('enddate')
        reason = request.POST.get('reason')

        # Validate date inputs
        if start and end:
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')

            if end_date < start_date:
                messages.error(request, "End date cannot be before start date.")
                return redirect('hallinoperabilitymanage')

        if inoperability_id:
            update_inoperability = get_object_or_404(Inoperability, id=inoperability_id)
            update_inoperability.hall = hall_obj
            update_inoperability.start_date = start
            update_inoperability.end_date = end
            update_inoperability.reason = reason
            update_inoperability.save()
        else:
            Inoperability.objects.create(hall=hall_obj, start_date=start, end_date=end, reason=reason)

        return redirect('hallinoperabilitymanage')

    hallname_list = [
        {
            'id': inoperability.id,
            'hall': inoperability.hall.name,
            'start': inoperability.start_date,
            'end': inoperability.end_date,
            'reason': inoperability.reason,
        }
        for inoperability in all_inoperability
    ]

    context = {
        'allhall': all_hall,
        'halllist': hallname_list,
        'updateinoperability': update_inoperability,
    }
    return render(request, 'hallinoperability.html', context)

def update_inoperability(request, id):
    update_inoperability = get_object_or_404(Inoperability, id=id)
    all_hall = Hall.objects.exclude(isdelete=1)
    all_inoperability = Inoperability.objects.exclude(isdelete=1).select_related('hall')

    hallname_list = [
        {
            'id': inoperability.id,
            'hall': inoperability.hall.name,
            'start': inoperability.start_date,
            'end': inoperability.end_date,
            'reason': inoperability.reason,
        }
        for inoperability in all_inoperability
    ]
    current_hall_name = update_inoperability.hall.name

    context = {
        'updateinoperability': update_inoperability,
        'halllist': hallname_list,
        'allhall': all_hall,
        'current_hall_name': current_hall_name,
    }
    return render(request, 'hallinoperability.html', context)

def delete_inoperability(request, id):
    delete_inoperability = get_object_or_404(Inoperability, id=id)
    delete_inoperability.isdelete = 1
    delete_inoperability.save()
    return redirect('hallinoperabilitymanage')




def paymentmanage(request):
    if request.method=="POST":
        paymentmode=request.POST.get('mode')
        total=request.POST.get('total')
        cash=request.POST.get('cash')
        remaining=request.POST.get('remaining')
        transaction=request.POST.get('transaction')
        payment_save=Payment(payment_mode=paymentmode,total_amount=total,cashreceived=cash,transaction_id=transaction,remaining_amount=remaining)
        payment_save.save()      
    return render(request,'hallpayment.html')



# def get_bookings(request, hall_id):
#     print("fdkf")
#     if request.method == 'GET':
#         bookings = Booking.objects.filter(hall=hall_id).values(
#              'date', 'timeslot', 'event_name', 'description', 'address', 'contact', 'ac'
#         )
#         print("hglhfl")
#         bookings_list = list(bookings)
#     return JsonResponse(bookings_list, safe=False)

def get_bookings(request, hall_id):
    print("hloooo")
    bookings = Booking.objects.filter(hall=hall_id).select_related('user', 'hall').values('date', 'timeslot','event_name', 'description', 'ac','user__name','user__address','user__number')
    print(list(bookings))
    return JsonResponse(list(bookings), safe=False)


def calendarview(request):
    return render(request, 'admin_calendar.html')

def cal(request):
    return render(request, 'hallcalendar.html')

def booked(request):
    Booked_list=Booking.objects.all()
    return render(request,'booklist.html',{'Booked_list':Booked_list})


def viewbooklist(request, id):
    booking = get_object_or_404(Booking, id=id)

    # Step 2: Split the features into a list of IDs
    feature_ids = booking.features.split(', ')

    # Step 3: Query the Feature table to get the names
    features = Feature.objects.filter(id__in=feature_ids).values_list('featurename', flat=True)
    
    # Step 4: Prepare the list of feature names
    feature_names = list(features)

    return render(request, 'view_bookinglist.html', {'Book': booking, 'feature_names': feature_names})


def approve(request, id):
    item = get_object_or_404(Booking, id=id)
    print(request.GET) 

    # Retrieve the approve_status parameter from the URL
    approve_status = request.GET.get('approve_status', '0')  # Default to '0' if not provided
    print(approve_status)
    # Ensure the value is a valid integer
    try:
        item.approval_status = int(approve_status)
        print(item.approval_status)
    except ValueError:
        # Log the error or handle it gracefully
        messages.error(request, "Invalid approval status.")
        return redirect(reverse('booked'))
    
    item.save()
    
    # Redirect to the desired URL after updating
    return redirect(reverse('booked'))



def logout(request):
    return HttpResponseRedirect(reverse('adminlogin'))

def inoperability_report(request):
    selected_hall = request.GET.get('hall')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    inoperabilities = Inoperability.objects.all()

    # Filter by hall if one is selected
    if selected_hall:
        inoperabilities = inoperabilities.filter(hall_id=selected_hall)

    # Filter by date range if both dates are provided
    if start_date and end_date:
        inoperabilities = inoperabilities.filter(
            start_date__gte=start_date,
            end_date__lte=end_date
        )

    # Pass filtered inoperabilities to the template
    context = {
        'inoperabilities': inoperabilities,
        'halls': Hall.objects.all(),
        'selected_hall': selected_hall,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'inoperability_report.html', context)



def generate_inoperability_pdf(request):
    selected_hall = request.GET.get('hall')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Start with all inoperabilities
    inoperabilities = Inoperability.objects.all()

    # Filter by hall if one is selected (and valid)
    if selected_hall and selected_hall.isdigit():
        inoperabilities = inoperabilities.filter(hall_id=selected_hall)

    # Filter by date range if both dates are provided
    if start_date and end_date:
        inoperabilities = inoperabilities.filter(
            start_date__gte=start_date,
            end_date__lte=end_date
        )

    # Debugging output
    print(f"Selected Hall: {selected_hall}, Start Date: {start_date}, End Date: {end_date}")
    print(f"Filtered Inoperabilities Count: {inoperabilities.count()}")

    # Create the response object for the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inoperability_report.pdf"'

    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Inoperability Report")

    p.setFont("Helvetica", 12)
    y_position = height - 100

    # Add inoperability records to the PDF
    if inoperabilities.exists():
        for inoperability in inoperabilities:
            details = (f"Hall: {inoperability.hall.name}, "
                        f"Start: {inoperability.start_date}, "
                        f"End: {inoperability.end_date}, "
                        f"Reason: {inoperability.reason}")
            p.drawString(100, y_position, details)
            y_position -= 20

            if y_position < 50:
                p.showPage()
                p.setFont("Helvetica", 12)
                y_position = height - 100
    else:
        p.drawString(100, y_position, "No inoperability records found for the selected criteria.")

    p.showPage()
    p.save()

    return response

def generate_individual_inoperability_pdf(request, id):
    inoperability = get_object_or_404(Inoperability, id=id)
    context = {
        'inoperability': inoperability,
    }
    html_string = render_to_string('individual_inoperability_pdf_template.html', context)
    
    # Create the response object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="inoperability_{id}.pdf"'

    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Add content to the PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Inoperability Details")

    p.setFont("Helvetica", 12)
    p.drawString(100, height - 100, f"Hall: {inoperability.hall.name}")
    p.drawString(100, height - 120, f"Start Date: {inoperability.start_date}")
    p.drawString(100, height - 140, f"End Date: {inoperability.end_date}")
    p.drawString(100, height - 160, f"Reason: {inoperability.reason}")

    p.showPage()
    p.save()

    return response
