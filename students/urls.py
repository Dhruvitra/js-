from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='dashboard'),
    path('students/', views.StudentListView.as_view(), name='student-list'),
    path('students/new/', views.StudentCreateView.as_view(), name='student-create'),
    path('courses/', views.course_list, name='course-list'),
    path('courses/<int:pk>/', views.course_detail, name='course-detail'),
    path('courses/<int:pk>/checkout/', views.checkout_view, name='checkout'),
    path('courses/<int:pk>/process-payment/', views.process_payment, name='process-payment'),
    path('courses/<int:course_pk>/video/<int:video_pk>/', views.watch_video, name='watch-video'),
    path('courses/<int:course_pk>/video/<int:video_pk>/complete/', views.mark_video_complete, name='mark-video-complete'),
    path('certificate/<uuid:uuid>/', views.certificate_view, name='certificate'),
    path('my-learning/', views.my_learning, name='my-learning'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
