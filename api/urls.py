from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home_alt'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    path('rating/', views.rating_view, name='rating'),
    path('news/', views.news_list_view, name='news_list'),
    path('schedule/', views.schedule_view, name='schedule'),

    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/add-grade/', views.add_grade, name='add_grade'),
    path('teacher/delete-grade/<int:grade_id>/', views.delete_grade, name='delete_grade'),
]