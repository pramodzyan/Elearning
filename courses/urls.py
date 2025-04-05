from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Common views
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Admin views
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/weeks/', views.manage_weeks, name='manage_weeks'),
    path('admin/weeks/create/', views.create_week, name='create_week'),
    path('admin/weeks/<int:week_id>/edit/', views.edit_week, name='edit_week'),
    path('admin/weeks/<int:week_id>/delete/', views.delete_week, name='delete_week'),
    path('admin/weeks/<int:week_id>/topics/', views.manage_topics, name='manage_topics'),
    path('admin/weeks/<int:week_id>/topics/create/', views.create_topic, name='create_topic'),
    path('admin/topics/<int:topic_id>/edit/', views.edit_topic, name='edit_topic'),
    path('admin/topics/<int:topic_id>/delete/', views.delete_topic, name='delete_topic'),
    path('admin/topics/<int:topic_id>/subtopics/', views.manage_subtopics, name='manage_subtopics'),
    path('admin/topics/<int:topic_id>/subtopics/create/', views.create_subtopic, name='create_subtopic'),
    path('admin/subtopics/<int:subtopic_id>/edit/', views.edit_subtopic, name='edit_subtopic'),
    path('admin/subtopics/<int:subtopic_id>/delete/', views.delete_subtopic, name='delete_subtopic'),
    path('admin/subtopics/<int:subtopic_id>/quizzes/', views.manage_quizzes, name='manage_quizzes'),
    path('admin/subtopics/<int:subtopic_id>/quizzes/create/', views.create_quiz, name='create_quiz'),
    path('admin/quizzes/<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('admin/quizzes/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('admin/quizzes/<int:quiz_id>/questions/', views.edit_quiz_questions, name='edit_quiz_questions'),
    path('admin/questions/<int:question_id>/choices/', views.edit_question_choices, name='edit_question_choices'),
    path('admin/performance/', views.student_performance, name='student_performance'),
    
    # Learner views
    path('learner/dashboard/', views.learner_dashboard, name='learner_dashboard'),
    path('learner/weeks/<int:week_id>/', views.week_detail, name='week_detail'),
    path('learner/subtopics/<int:subtopic_id>/', views.subtopic_detail, name='subtopic_detail'),
    path('learner/quizzes/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('learner/attempts/<int:attempt_id>/results/', views.quiz_results, name='quiz_results'),
]
