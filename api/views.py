from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import (
    Student, Teacher, ClassRoom, Subject, Grade,
    WeeklyRating, News, Event, InviteCode
)

User = get_user_model()


def calculate_class_rating(week_start, week_end):
    classes = ClassRoom.objects.all()
    rating_data = []

    for cls in classes:
        students = Student.objects.filter(classroom=cls)
        total_percent = 0
        count_with_grades = 0

        for student in students:
            grades = Grade.objects.filter(
                student=student,
                date__date__gte=week_start,
                date__date__lte=week_end
            )
            if grades.exists():
                student_avg = sum(g.get_percent() for g in grades) / grades.count()
                total_percent += student_avg
                count_with_grades += 1

        class_avg = (total_percent / count_with_grades) if count_with_grades > 0 else 0

        rating_data.append({
            'class': cls,
            'average': round(class_avg, 1),
            'student_count': students.count(),
        })

    rating_data.sort(key=lambda x: x['average'], reverse=True)

    for i, item in enumerate(rating_data):
        if i == 0:
            item['medal'] = '🥇'
        elif i == 1:
            item['medal'] = '🥈'
        elif i == 2:
            item['medal'] = '🥉'
        else:
            item['medal'] = str(i + 1)

    return rating_data


def get_current_week():
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def home(request):
    if not request.user.is_authenticated:
        return redirect('register')

    week_start, week_end = get_current_week()
    rating_data = calculate_class_rating(week_start, week_end)
    top_rating = [item for item in rating_data if item['student_count'] > 0][:5]

    student = None
    user_score = None
    class_avg_score = None

    try:
        student = Student.objects.get(user=request.user)
        grades = Grade.objects.filter(student=student)
        if grades.exists():
            user_score = round(sum(g.get_percent() for g in grades) / grades.count(), 1)

        class_students = Student.objects.filter(classroom=student.classroom)
        if class_students.exists():
            all_grades = Grade.objects.filter(student__in=class_students)
            if all_grades.exists():
                class_avg_score = round(sum(g.get_percent() for g in all_grades) / all_grades.count(), 1)
    except Student.DoesNotExist:
        pass

    news_list = News.objects.all().order_by('-created_at')[:2]

    context = {
        'rating_data': top_rating,
        'week_start': week_start,
        'week_end': week_end,
        'student': student,
        'user_score': user_score,
        'class_avg_score': class_avg_score,
        'news_list': news_list,
    }
    return render(request, 'home.html', context)


@ensure_csrf_cookie
def register_view(request):
    if request.method == 'POST':
        first_name = (request.POST.get('first_name') or '').strip()
        reg_code = (request.POST.get('reg_code') or '').strip()

        if not first_name:
            messages.error(request, '❌ Введите имя!')
            return render(request, 'register.html')

        if not reg_code.isdigit() or len(reg_code) != 13:
            messages.error(request, '❌ Код должен быть ровно 13 цифр!')
            return render(request, 'register.html')

        try:
            invite = InviteCode.objects.get(code=reg_code, is_used=False)
        except InviteCode.DoesNotExist:
            messages.error(request, '❌ Неверный или уже использованный код!')
            return render(request, 'register.html')

        if User.objects.filter(username=reg_code).exists():
            messages.error(request, '❌ Этот код уже зарегистрирован!')
            return render(request, 'register.html')

        user = User.objects.create_user(
            username=reg_code,
            password=reg_code,
            first_name=first_name,
            last_name=''
        )

        role = invite.role

        if role == 'student':
            if not invite.classroom:
                messages.error(request, '❌ Код ученика не привязан к классу.')
                user.delete()
                return render(request, 'register.html')
            Student.objects.create(user=user, classroom=invite.classroom)
        elif role == 'teacher':
            Teacher.objects.create(user=user)

        invite.is_used = True
        invite.save()

        login(request, user)

        if role == 'student':
            return redirect('student_dashboard')
        else:
            return redirect('teacher_dashboard')

    return render(request, 'register.html')


@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'student_profile'):
                return redirect('student_dashboard')
            elif hasattr(user, 'teacher_profile'):
                return redirect('teacher_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, '❌ Неверный логин или пароль')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def student_dashboard(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return render(request, 'error.html', {'message': 'Вы не являетесь учеником'})

    grades = Grade.objects.filter(student=student).select_related('subject', 'teacher__user').order_by('-date')

    avg_score = None
    if grades.exists():
        avg_score = round(sum(g.get_percent() for g in grades) / grades.count(), 1)

    context = {
        'student': student,
        'grades': grades,
        'avg_score': avg_score,
    }
    return render(request, 'students/student_dashboard.html', context)


import json  # добавьте в начало файла, если ещё нет

@login_required
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return render(request, 'error.html', {'message': 'Вы не являетесь учителем'})

    # Собираем данные о классах и их учениках для JS-фильтрации
    classes_data = {}
    for cls in ClassRoom.objects.all():
        students = Student.objects.filter(classroom=cls).select_related('user')
        classes_data[str(cls.id)] = {
            'name': cls.name,
            'students': [
                {
                    'id': s.id,
                    'name': (f"{s.user.first_name} {s.user.last_name}".strip() or s.user.username)
                }
                for s in students
            ]
        }

    subjects = Subject.objects.all()
    recent_grades = Grade.objects.filter(teacher=teacher).select_related(
        'student__user', 'subject'
    ).order_by('-date')[:15]

    context = {
        'teacher': teacher,
        'all_classes': ClassRoom.objects.all(),
        'classes_data_json': json.dumps(classes_data, ensure_ascii=False),
        'subjects': subjects,
        'recent_grades': recent_grades,
    }
    return render(request, 'teachers/teacher_dashboard.html', context)
@login_required
def add_grade(request):
    if request.method == 'POST':
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            messages.error(request, 'У вас нет прав ставить оценки')
            return redirect('teacher_dashboard')

        subject_id = request.POST.get('subject_id')
        student_id = request.POST.get('student_id')
        grade_value = request.POST.get('grade')

        if grade_value not in ('2', '3', '4', '5'):
            messages.error(request, 'Оценка должна быть от 2 до 5')
            return redirect('teacher_dashboard')

        subject = get_object_or_404(Subject, id=subject_id)
        student = get_object_or_404(Student, id=student_id)

        Grade.objects.create(
            student=student,
            subject=subject,
            teacher=teacher,
            grade=int(grade_value)
        )
        messages.success(request, f'Оценка {grade_value} поставлена ученику {student.user.first_name}!')
        return redirect('teacher_dashboard')

    return redirect('teacher_dashboard')


@login_required
def delete_grade(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    if grade.teacher.user == request.user:
        grade.delete()
        messages.success(request, 'Оценка удалена')
    else:
        messages.error(request, 'Нет прав на удаление этой оценки')
    return redirect('teacher_dashboard')


@login_required
def profile_view(request):
    """Личный кабинет пользователя с оценками и рейтингом"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        if first_name:
            request.user.first_name = first_name
            request.user.save()
            messages.success(request, 'Имя обновлено!')
            return redirect('profile')

    user = request.user
    student = None
    teacher = None
    user_score = None
    class_avg_score = None
    class_position = None
    total_classes = None
    grades = []
    recent_grades = []

    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        pass

    try:
        teacher = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        pass

    if student:
        user_grades = Grade.objects.filter(student=student)
        if user_grades.exists():
            user_score = round(sum(g.get_percent() for g in user_grades) / user_grades.count(), 1)

        class_students = Student.objects.filter(classroom=student.classroom)
        if class_students.exists():
            all_class_grades = Grade.objects.filter(student__in=class_students)
            if all_class_grades.exists():
                class_avg_score = round(sum(g.get_percent() for g in all_class_grades) / all_class_grades.count(), 1)

        grades = Grade.objects.filter(student=student).select_related('subject').order_by('-date')[:10]

        # Место класса в рейтинге
        all_classes = ClassRoom.objects.all()
        class_ratings = []
        for cls in all_classes:
            cls_students = Student.objects.filter(classroom=cls)
            if not cls_students.exists():
                continue
            cls_grades = Grade.objects.filter(student__in=cls_students)
            if cls_grades.exists():
                avg = round(sum(g.get_percent() for g in cls_grades) / cls_grades.count(), 1)
            else:
                avg = 0
            class_ratings.append({'class': cls, 'average': avg})
        class_ratings.sort(key=lambda x: x['average'], reverse=True)
        total_classes = len(class_ratings)
        for i, item in enumerate(class_ratings):
            if item['class'] == student.classroom:
                class_position = i + 1
                break

    if teacher:
        recent_grades = Grade.objects.filter(teacher=teacher).select_related('student__user', 'subject').order_by('-date')[:10]

    context = {
        'user': user,
        'student': student,
        'teacher': teacher,
        'user_score': user_score,
        'class_avg_score': class_avg_score,
        'class_position': class_position,
        'total_classes': total_classes,
        'grades': grades,
        'recent_grades': recent_grades,
    }
    return render(request, 'profile.html', context)


# ==================== РАСПИСАНИЕ ====================
def schedule_view(request):
    return render(request, 'schedule.html')


# ==================== ВСЕ НОВОСТИ ====================
def news_list_view(request):
    news_list = News.objects.all().order_by('-created_at')
    return render(request, 'news_list.html', {'news_list': news_list})


# ==================== ПОЛНЫЙ РЕЙТИНГ ====================
def rating_view(request):
    week_start, week_end = get_current_week()
    rating_data = calculate_class_rating(week_start, week_end)
    # оставляем только классы с учениками
    rating_data = [item for item in rating_data if item['student_count'] > 0]
    return render(request, 'rating.html', {'rating_data': rating_data})