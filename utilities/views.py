from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.dispatch import receiver
from django.db import IntegrityError
from .models import Utility
from .forms import UtilityForm
from aws_utils import (
    upload_utility_file,
    add_utility_record,
    delete_utility_record,
    send_utility_task,
    create_utility_queue,
    publish_utility_alert
)
from decimal import Decimal
import boto3, os
from botocore.exceptions import ClientError
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:263072075949:utility-alerts-topic-2025'
sns = boto3.client('sns')

def generate_presigned_url(s3_key, expiration=3600):
    s3_client = boto3.client('s3', region_name='us-east-1')
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': 'utility-management-files-2025',
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None

def send_admin_notification(subject, message):
    try:
        publish_utility_alert(SNS_TOPIC_ARN, f"{subject}\n\n{message}")
        return True
    except Exception:
        return False

def send_user_utility_notification(user, action, utility):
    try:
        user_email = user.email
        if not user_email:
            return False
        if action == 'created':
            subject = f"Utility Record Created - {utility.type.title()}"
            message = f"Hello {user.username},\nYour utility record was created."
        elif action == 'edited':
            subject = f"Utility Record Updated - {utility.type.title()}"
            message = f"Hello {user.username},\nYour utility record was updated."
        elif action == 'deleted':
            subject = f"Utility Record Deleted - {utility.type.title()}"
            message = f"Hello {user.username},\nYour utility record was deleted."
        else:
            return False
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email], fail_silently=False)
        return True
    except Exception:
        return False

@login_required
def dashboard(request):
    utilities = Utility.objects.filter(user=request.user)
    
    for utility in utilities:
        if utility.file_s3_key:
            utility.presigned_url = generate_presigned_url(utility.file_s3_key)
    
    return render(request, 'utilities/dashboard.html', {'utilities': utilities})

@login_required
def utility_create(request):
    if request.method == 'POST':
        form = UtilityForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            
            if request.FILES.get('file'):
                file_obj = request.FILES['file']
                file_path = f'/tmp/{file_obj.name}'
                
                try:
                    # Save file locally first
                    with open(file_path, 'wb+') as f:
                        for chunk in file_obj.chunks():
                            f.write(chunk)
                    
                    # Upload to S3
                    s3_key = f'uploads/{instance.type}/{file_obj.name}'
                    print(f"Uploading to S3: {s3_key}")
                    
                    upload_success = upload_utility_file(file_path, s3_key)
                    
                    if upload_success:
                        instance.file_s3_key = s3_key
                        print(f"Upload successful: {s3_key}")

                        # ========== LAMBDA INVOCATION HERE ==========
                        payload = {
                            'bucket': 'utility-management-files-2025',
                            'key': s3_key,
                            'user_id': request.user.id,
                            'action': 'file_upload'
                        }
                        lambda_client.invoke(
                            FunctionName='utility-file-processor',  # Use your Lambda function name or ARN
                            InvocationType='Event',  # Async
                            Payload=json.dumps(payload)
                        )
                        print("Lambda function triggered for file processing.")
                        # ========== END LAMBDA INVOCATION ==========
                    else:
                        print(f"Upload failed for: {s3_key}")
                        instance.file_s3_key = None
                    
                    # Clean up temp file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        
                except Exception as e:
                    print(f"Error during file upload: {e}")
                    instance.file_s3_key = None
            
            instance.user = request.user
            instance.save()
            
            send_user_utility_notification(request.user, 'created', instance)
            add_utility_record(instance.id, instance.type, Decimal(str(instance.usage)), str(instance.date), instance.notes or '')
            
            queue_url = create_utility_queue()
            msg = f"New utility record created: type={instance.type}, usage={instance.usage}, date={instance.date}, id=util-{instance.id}, user_email={request.user.email}"
            send_utility_task(queue_url, msg)
            
            return redirect('dashboard')
    else:
        form = UtilityForm()
    return render(request, 'utilities/utility_form.html', {'form': form})

@login_required
def utility_edit(request, pk):
    utility = get_object_or_404(Utility, pk=pk, user=request.user)
    if request.method == 'POST':
        form = UtilityForm(request.POST, request.FILES, instance=utility)
        if form.is_valid():
            instance = form.save(commit=False)
            if request.FILES.get('file'):
                file_obj = request.FILES['file']
                file_path = f'/tmp/{file_obj.name}'
                with open(file_path, 'wb+') as f:
                    for chunk in file_obj.chunks():
                        f.write(chunk)
                s3_key = f'uploads/{instance.type}/{file_obj.name}'
                upload_utility_file(file_path, s3_key)
                instance.file_s3_key = s3_key
                os.remove(file_path)
                
                # ========== LAMBDA INVOCATION HERE ==========
                payload = {
                    'bucket': 'utility-management-files-2025',
                    'key': s3_key,
                    'user_id': request.user.id,
                    'action': 'file_edit'
                }
                lambda_client.invoke(
                    FunctionName='utility-file-processor',
                    InvocationType='Event',
                    Payload=json.dumps(payload)
                )
                print("Lambda function triggered for file edit.")
                # ========== END LAMBDA INVOCATION ==========
            instance.user = request.user
            instance.save()
            send_user_utility_notification(request.user, 'edited', instance)
            queue_url = create_utility_queue()
            msg = f"Utility record edited: type={instance.type}, usage={instance.usage}, date={instance.date}, id=util-{instance.id}, user_email={request.user.email}"
            send_utility_task(queue_url, msg)
            return redirect('dashboard')
    else:
        form = UtilityForm(instance=utility)
    return render(request, 'utilities/utility_form.html', {'form': form})

@login_required
def utility_delete(request, pk):
    utility = get_object_or_404(Utility, pk=pk, user=request.user)
    send_user_utility_notification(request.user, 'deleted', utility)
    queue_url = create_utility_queue()
    msg = f"Utility record deleted: type={utility.type}, usage={utility.usage}, date={utility.date}, id=util-{utility.id}, user_email={request.user.email}"
    send_utility_task(queue_url, msg)
    delete_utility_record(pk)
    utility.delete()
    return redirect('dashboard')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                error = "Invalid email or password"
                return render(request, 'registration/login.html', {'error': error})
        except User.DoesNotExist:
            error = "No account found with this email"
            return render(request, 'registration/login.html', {'error': error})
    return render(request, 'registration/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        errors = []
        if not username:
            errors.append("Username is required")
        if not email:
            errors.append("Email is required")
        if not password1:
            errors.append("Password is required")
        if password1 != password2:
            errors.append("Passwords do not match")
        if len(password1) < 8:
            errors.append("Password must be at least 8 characters")
        if User.objects.filter(username=username).exists():
            errors.append("Username already taken")
        if User.objects.filter(email=email).exists():
            errors.append("Email already registered")
        if errors:
            return render(request, 'registration/signup.html', {
                'errors': errors,
                'username': username,
                'email': email
            })
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            send_mail(
                'Welcome to Utility Management System!',
                f"Hello {user.username}, your account has been created.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            subject = "New User Registered"
            message = f"A new user has registered, username={user.username}, email={user.email}"
            send_admin_notification(subject, message)
            login(request, user)
            return redirect('dashboard')
        except IntegrityError:
            errors.append("An error occurred. Please try again.")
            return render(request, 'registration/signup.html', {
                'errors': errors,
                'username': username,
                'email': email
            })
    return render(request, 'registration/signup.html')

@receiver(user_logged_in)
def notify_admin_on_login(sender, request, user, **kwargs):
    subject = "User Logged In"
    message = f"A user has logged in: {user.username}, {user.email}"
    send_admin_notification(subject, message)

def custom_password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = User.objects.filter(email=email)
            for user in users:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                domain = request.get_host()
                protocol = 'https' if request.is_secure() else 'http'
                reset_url = f"{protocol}://{domain}/password-reset-confirm/{uid}/{token}/"
                subject = 'Password Reset for Utility Management System'
                message = f"Hello {user.username}, use this link to reset your password: {reset_url}"
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()
    return render(request, 'registration/password_reset_form.html', {'form': form})
