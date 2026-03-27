from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Student, Course, Department, Enrollment, CourseVideo, VideoProgress, Certificate
import uuid

# ─────────────────────────────────────────
# HOME / DASHBOARD
# ─────────────────────────────────────────
def home(request):
    dept_count = Department.objects.count()
    student_count = Student.objects.count()
    course_count = Course.objects.count()

    featured_courses = Course.objects.filter(is_featured=True).select_related('department')[:6]
    all_courses = Course.objects.all().select_related('department')[:9]

    steps = [
        {'icon': '🔍', 'title': 'Find Your Course', 'desc': 'Browse thousands of courses across all skill levels and subject areas.'},
        {'icon': '🎓', 'title': 'Learn at Your Pace', 'desc': 'Watch expert video lessons anytime, anywhere, on any device.'},
        {'icon': '📜', 'title': 'Earn a Certificate', 'desc': 'Complete your course and receive a verified certificate to showcase your skills.'},
    ]

    context = {
        'dept_count': dept_count,
        'student_count': student_count,
        'course_count': course_count,
        'featured_courses': featured_courses,
        'all_courses': all_courses,
        'steps': steps,
    }
    return render(request, 'students/dashboard.html', context)

# ─────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')

        if not email or not password or not fname:
            messages.error(request, "All fields are required.")
            return redirect('signup')

        if User.objects.filter(username=email).exists():
            messages.error(request, "An account with that email already exists.")
            return redirect('signup')

        user = User.objects.create_user(username=email, email=email, password=password, first_name=fname, last_name=lname)

        import random
        generated_id = f"STU-{random.randint(10000, 99999)}"
        Student.objects.create(user=user, first_name=fname, last_name=lname, email=email, enrollment_number=generated_id)

        login(request, user)
        messages.success(request, f"Welcome, {fname}! Your account is ready. Start exploring courses!")
        return redirect('dashboard')

    return render(request, 'students/signup.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid email or password. Please try again.")
    return render(request, 'students/login.html')


def logout_view(request):
    logout(request)
    return redirect('dashboard')

# ─────────────────────────────────────────
# STUDENT VIEWS
# ─────────────────────────────────────────
class StudentListView(ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'

class StudentCreateView(CreateView):
    model = Student
    fields = ['first_name', 'last_name', 'date_of_birth', 'email', 'enrollment_number', 'department']
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student-list')

# ─────────────────────────────────────────
# COURSE CATALOG
# ─────────────────────────────────────────
def course_list(request):
    courses = Course.objects.all().select_related('department').prefetch_related('videos')
    departments = Department.objects.all()

    q = request.GET.get('q', '').strip()
    dept_id = request.GET.get('dept', '')
    level = request.GET.get('level', '')

    if q:
        courses = courses.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(instructor_name__icontains=q))
    if dept_id:
        courses = courses.filter(department_id=dept_id)
    if level:
        courses = courses.filter(level=level)

    return render(request, 'students/course_list.html', {
        'courses': courses,
        'departments': departments,
    })

# ─────────────────────────────────────────
# COURSE DETAIL
# ─────────────────────────────────────────
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    selected_student = getattr(request.user, 'student', None) if request.user.is_authenticated else None

    is_enrolled = False
    progress_map = {}
    certificate = None

    if selected_student:
        is_enrolled = Enrollment.objects.filter(student=selected_student, course=course).exists()
        if is_enrolled:
            for vp in VideoProgress.objects.filter(student=selected_student, video__course=course):
                progress_map[vp.video_id] = vp.is_completed
            certificate = Certificate.objects.filter(student=selected_student, course=course).first()

    videos = course.videos.all()
    grouped_videos = {}
    for choice in CourseVideo.LEVEL_CHOICES:
        level_name = choice[0]
        level_videos = videos.filter(level=level_name)
        if level_videos.exists():
            videos_list = list(level_videos)
            for vid in videos_list:
                vid.is_completed = progress_map.get(vid.id, False)
            grouped_videos[level_name] = videos_list

    context = {
        'course': course,
        'grouped_videos': grouped_videos,
        'selected_student': selected_student,
        'is_enrolled': is_enrolled,
        'certificate': certificate,
        'total_videos': videos.count(),
    }
    return render(request, 'students/course_detail.html', context)

# ─────────────────────────────────────────
# MY LEARNING DASHBOARD
# ─────────────────────────────────────────
@login_required(login_url='login')
def my_learning(request):
    student = getattr(request.user, 'student', None)
    if not student:
        messages.error(request, "No student profile found for your account.")
        return redirect('dashboard')

    raw_enrollments = Enrollment.objects.filter(student=student).select_related('course__department').order_by('-date_enrolled')
    
    enrollments_data = []
    for enrollment in raw_enrollments:
        course = enrollment.course
        total_videos = course.videos.count()
        completed_count = VideoProgress.objects.filter(student=student, video__course=course, is_completed=True).count()
        progress = int((completed_count / total_videos * 100)) if total_videos > 0 else 0
        enrollments_data.append({
            'course': course,
            'enrollment': enrollment,
            'total_videos': total_videos,
            'completed_count': completed_count,
            'progress': progress,
        })

    certificates = Certificate.objects.filter(student=student).select_related('course')
    completed_videos = VideoProgress.objects.filter(student=student, is_completed=True).count()

    return render(request, 'students/my_learning.html', {
        'student': student,
        'enrollments': enrollments_data,
        'certificates': certificates,
        'completed_videos': completed_videos,
    })

# ─────────────────────────────────────────
# CHECKOUT / PAYMENT
# ─────────────────────────────────────────
@login_required(login_url='login')
def checkout_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    student = getattr(request.user, 'student', None)
    if not student:
        messages.error(request, "No student profile found for your account.")
        return redirect('course-detail', pk=pk)
    if Enrollment.objects.filter(student=student, course=course).exists():
        messages.info(request, "You are already enrolled in this course.")
        return redirect('course-detail', pk=pk)
    return render(request, 'students/checkout.html', {'course': course, 'student': student})


@login_required(login_url='login')
def process_payment(request, pk):
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=pk)
        student = getattr(request.user, 'student', None)
        if not student:
            return redirect('login')
        import time
        time.sleep(1.5)
        Enrollment.objects.get_or_create(student=student, course=course)
        messages.success(request, f"🎉 Payment successful! You are now enrolled in '{course.name}'. Start learning!")
        return redirect('course-detail', pk=pk)
    return redirect('course-detail', pk=pk)

# ─────────────────────────────────────────
# VIDEO PLAYER
# ─────────────────────────────────────────
@login_required(login_url='login')
def watch_video(request, course_pk, video_pk):
    course = get_object_or_404(Course, pk=course_pk)
    video = get_object_or_404(CourseVideo, pk=video_pk, course=course)
    student = getattr(request.user, 'student', None)

    if not student or not Enrollment.objects.filter(student=student, course=course).exists():
        messages.error(request, "Please enroll in this course to access the content.")
        return redirect('course-detail', pk=course_pk)

    vp, _ = VideoProgress.objects.get_or_create(student=student, video=video)
    
    # Get adjacent videos for navigation
    all_videos = list(course.videos.all())
    current_idx = next((i for i, v in enumerate(all_videos) if v.pk == video.pk), 0)
    prev_video = all_videos[current_idx - 1] if current_idx > 0 else None
    next_video = all_videos[current_idx + 1] if current_idx < len(all_videos) - 1 else None

    context = {
        'course': course,
        'video': video,
        'selected_student': student,
        'is_completed': vp.is_completed,
        'prev_video': prev_video,
        'next_video': next_video,
        'all_videos': all_videos,
        'current_idx': current_idx,
    }
    return render(request, 'students/video_player.html', context)


@login_required(login_url='login')
def mark_video_complete(request, course_pk, video_pk):
    if request.method == 'POST':
        student = getattr(request.user, 'student', None)
        course = get_object_or_404(Course, pk=course_pk)
        video = get_object_or_404(CourseVideo, pk=video_pk, course=course)
        if not student:
            return redirect('login')

        vp, _ = VideoProgress.objects.get_or_create(student=student, video=video)
        vp.is_completed = True
        vp.save()

        total = course.videos.count()
        completed = VideoProgress.objects.filter(student=student, video__course=course, is_completed=True).count()

        if total > 0 and completed == total:
            cert, created = Certificate.objects.get_or_create(student=student, course=course)
            if created:
                messages.success(request, f"🏆 Congratulations! You completed '{course.name}' and earned a verified certificate!")
        else:
            messages.success(request, f"✅ Lesson '{video.title}' marked as complete! ({completed}/{total})")

        return redirect('course-detail', pk=course_pk)
    return redirect('dashboard')


def certificate_view(request, uuid):
    certificate = get_object_or_404(Certificate, certificate_code=uuid)
    return render(request, 'students/certificate.html', {'certificate': certificate})
