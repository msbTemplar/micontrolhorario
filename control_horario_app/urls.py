"""
URL configuration for website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    
  
    path('set_cookie_consent/', views.set_cookie_consent, name='set_cookie_consent'),
    
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('timesheet/', views.timesheet_view, name='timesheet'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('export-timesheet-csv/', views.export_timesheet_csv, name='export_timesheet_csv'), # NUEVA LÍNEA
    path('export-timesheet-xlsx/', views.export_timesheet_xlsx, name='export_timesheet_xlsx'), # NUEVA LÍNEA
    path('export-timesheet-pdf/', views.export_timesheet_pdf, name='export_timesheet_pdf'), # NUEVA LÍNEA
    # NUEVAS URLs para Edición y Eliminación
    path('edit-entry/<int:entry_id>/', views.edit_time_entry, name='edit_time_entry'),
    path('delete-entry/<int:entry_id>/', views.delete_time_entry, name='delete_time_entry'),
    
    # NUEVAS URLs para Gestión de Perfil
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('admin-requests/', views.admin_modification_requests, name='admin_modification_requests'),
    path('review-request/<int:request_id>/', views.review_modification_request, name='review_modification_request_detail'),



    





]
