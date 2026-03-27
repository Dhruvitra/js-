from django.contrib import admin
from .models import Department, Course, Student, Enrollment

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'duration_months')
    list_filter = ('department',)
    search_fields = ('name',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'enrollment_number', 'department', 'email')
    list_filter = ('department',)
    search_fields = ('first_name', 'last_name', 'enrollment_number', 'email')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date_enrolled')
    list_filter = ('course', 'date_enrolled')

from .models import CourseVideo, VideoProgress, Certificate

@admin.register(CourseVideo)
class CourseVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'level', 'order')
    list_filter = ('course', 'level')
    ordering = ('course', 'level', 'order')

@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'video', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'video__course')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'issued_on', 'certificate_code')
    list_filter = ('course', 'issued_on')
    readonly_fields = ('certificate_code', 'issued_on')
