from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    # path('quiz_page/', views.quiz_page, name='quiz_page'),
     path("student/", views.student_dashboard, name="student_dashboard"),
    path("get-chapters/<int:subject_id>/", views.get_chapters, name="get_chapters"),
    # path("quiz/<int:subject_id>/<int:chapter_id>/", views.take_quiz, name="take_quiz"),

     path("quiz/<int:subject_id>/<int:chapter_id>/start/", views.quiz_start, name="quiz_start"),

    # one-question pages
    path("quiz/<int:subject_id>/<int:chapter_id>/<int:q_no>/", views.quiz_question, name="quiz_question"),

    # result
    path("quiz/<int:subject_id>/<int:chapter_id>/result/<int:attempt_id>/", views.quiz_result, name="quiz_result"),
    
]
