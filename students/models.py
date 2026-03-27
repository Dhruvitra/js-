from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    LEVEL_CHOICES = (
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Mixed', 'Mixed'),
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    what_you_learn = models.TextField(blank=True, null=True, help_text="Newline-separated list of learning outcomes")
    duration_months = models.IntegerField(help_text="Duration in months")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=99.00, help_text="Course unlock price in USD")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Beginner')
    instructor_name = models.CharField(max_length=150, default='EduManage Instructor')
    thumbnail_url = models.URLField(blank=True, null=True, help_text="URL of the course cover image")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    total_reviews = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False, help_text="Show on homepage featured section")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')

    def __str__(self):
        return self.name
    
    def get_stars_range(self):
        """Returns a list for rendering filled/empty stars"""
        full = int(self.rating)
        return {'full': range(full), 'empty': range(5 - full)}

from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='student')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True)
    enrollment_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.enrollment_number})"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    date_enrolled = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"

class CourseVideo(models.Model):
    LEVEL_CHOICES = (
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES, default='Beginner')
    youtube_embed_url = models.URLField(help_text="Embed link (e.g. https://www.youtube.com/embed/...)")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['level', 'order']

    def __str__(self):
        return f"{self.title} ({self.level})"

class VideoProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='video_progress')
    video = models.ForeignKey(CourseVideo, on_delete=models.CASCADE, related_name='completions')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'video')

    def __str__(self):
        return f"{self.student} progress on {self.video}"

import uuid
class Certificate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_on = models.DateTimeField(auto_now_add=True)
    certificate_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"Certificate - {self.course.name} - {self.student}"
