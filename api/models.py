from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    def __str__(self):
        return self.username


class ClassRoom(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    homeroom_class = models.OneToOneField(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='homeroom_teacher')

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='students')

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"


class Grade(models.Model):
    GRADE_CHOICES = [(2, '2'), (3, '3'), (4, '4'), (5, '5')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='grades')
    grade = models.PositiveSmallIntegerField(choices=GRADE_CHOICES)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.name} - {self.grade}"

    def get_percent(self):
        return {2: 40, 3: 60, 4: 80, 5: 100}.get(self.grade, 0)


class WeeklyRating(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='ratings')
    week_start = models.DateField()
    week_end = models.DateField()
    average_percent = models.FloatField()
    rank = models.IntegerField()

    class Meta:
        ordering = ['-week_start', 'rank']


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"


class InviteCode(models.Model):
    ROLE_CHOICES = [
        ('student', 'Ученик'),
        ('teacher', 'Учитель'),
    ]
    code = models.CharField(max_length=13, unique=True, verbose_name="Код (13 цифр)")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="Роль")
    classroom = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Класс (для ученика)")
    is_used = models.BooleanField(default=False, verbose_name="Использован")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    def __str__(self):
        return f"{self.code} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Пригласительный код"
        verbose_name_plural = "Пригласительные коды"