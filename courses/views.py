from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg, F, Q, Max
from django.views.decorators.csrf import csrf_protect
from .models import (
    UserProfile, Week, Topic, Subtopic, Quiz, Question, 
    Choice, QuizAttempt, QuizResponse, TopicProgress
)
from .forms import (
    UserRegistrationForm, WeekForm, TopicForm, SubtopicForm, 
    QuizForm, QuestionForm, ChoiceFormSet, QuestionFormSet, QuizResponseForm
)

def home(request):
    """Home page view"""
    weeks = Week.objects.all()
    return render(request, 'home.html', {'weeks': weeks})

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            # Create the user profile with the selected role
            UserProfile.objects.create(user=user, role=role)
            login(request, user)
            messages.success(request, f'Account created successfully. You are now logged in as {user.username}.')
            
            # Redirect based on role
            if role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('learner_dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@csrf_protect
def custom_logout(request):
    """Custom logout view with proper CSRF protection"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('home')
    # For GET requests, show the logout confirmation page
    return render(request, 'registration/logout.html')

# Helper function to check if user is admin
def is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'admin'

# Helper function to check if user is learner
def is_learner(user):
    return hasattr(user, 'profile') and user.profile.role == 'learner'

# Admin views
@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    # Count statistics
    weeks_count = Week.objects.count()
    topics_count = Topic.objects.count()
    subtopics_count = Subtopic.objects.count()
    quizzes_count = Quiz.objects.count()
    learners_count = UserProfile.objects.filter(role='learner').count()
    quiz_attempts = QuizAttempt.objects.count()
    
    # Get average score across all quizzes
    avg_score = QuizAttempt.objects.aggregate(avg=Avg('percentage'))['avg'] or 0
    
    # Get recent quiz attempts
    recent_attempts = QuizAttempt.objects.select_related('user', 'quiz').order_by('-completed_at')[:10]
    
    # Get lists for dropdown menus - limited to most recent items to keep menus manageable
    weeks = Week.objects.all().order_by('order')
    topics = Topic.objects.select_related('week').order_by('week__order', 'order')[:20]
    subtopics = Subtopic.objects.select_related('topic', 'topic__week').order_by(
        'topic__week__order', 'topic__order', 'order'
    )[:20]
    
    context = {
        # Statistics counts
        'weeks_count': weeks_count,
        'topics_count': topics_count,
        'subtopics_count': subtopics_count,
        'quizzes_count': quizzes_count,
        'learners_count': learners_count,
        'quiz_attempts': quiz_attempts,
        'avg_score': avg_score,
        'recent_attempts': recent_attempts,
        
        # Lists for dropdown menus
        'weeks': weeks,
        'topics': topics,
        'subtopics': subtopics
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
def manage_weeks(request):
    """View to manage weeks"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    weeks = Week.objects.all().order_by('order')
    return render(request, 'admin/manage_weeks.html', {'weeks': weeks})

@login_required
def create_week(request):
    """View to create a new week"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    if request.method == 'POST':
        form = WeekForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Week created successfully.')
            return redirect('manage_weeks')
    else:
        form = WeekForm()
    
    return render(request, 'admin/edit_week.html', {'form': form, 'is_new': True})

@login_required
def edit_week(request, week_id):
    """View to edit an existing week"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    week = get_object_or_404(Week, id=week_id)
    
    if request.method == 'POST':
        form = WeekForm(request.POST, instance=week)
        if form.is_valid():
            form.save()
            messages.success(request, 'Week updated successfully.')
            return redirect('manage_weeks')
    else:
        form = WeekForm(instance=week)
    
    return render(request, 'admin/edit_week.html', {'form': form, 'week': week, 'is_new': False})

@login_required
def delete_week(request, week_id):
    """View to delete a week"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    week = get_object_or_404(Week, id=week_id)
    
    if request.method == 'POST':
        week.delete()
        messages.success(request, 'Week deleted successfully.')
        return redirect('manage_weeks')
    
    return render(request, 'admin/delete_confirmation.html', {'object': week, 'object_type': 'Week'})

@login_required
def manage_topics(request, week_id):
    """View to manage topics for a specific week"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    week = get_object_or_404(Week, id=week_id)
    topics = Topic.objects.filter(week=week).order_by('order')
    
    return render(request, 'admin/manage_topics.html', {'week': week, 'topics': topics})

@login_required
def create_topic(request, week_id):
    """View to create a new topic for a specific week"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    week = get_object_or_404(Week, id=week_id)
    
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.week = week
            topic.save()
            messages.success(request, 'Topic created successfully.')
            return redirect('manage_topics', week_id=week.id)
    else:
        form = TopicForm(initial={'week': week})
    
    return render(request, 'admin/edit_topic.html', {'form': form, 'week': week, 'is_new': True})

@login_required
def edit_topic(request, topic_id):
    """View to edit an existing topic"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    topic = get_object_or_404(Topic, id=topic_id)
    
    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Topic updated successfully.')
            return redirect('manage_topics', week_id=topic.week.id)
    else:
        form = TopicForm(instance=topic)
    
    return render(request, 'admin/edit_topic.html', {'form': form, 'topic': topic, 'week': topic.week, 'is_new': False})

@login_required
def delete_topic(request, topic_id):
    """View to delete a topic"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    topic = get_object_or_404(Topic, id=topic_id)
    week_id = topic.week.id
    
    if request.method == 'POST':
        topic.delete()
        messages.success(request, 'Topic deleted successfully.')
        return redirect('manage_topics', week_id=week_id)
    
    return render(request, 'admin/delete_confirmation.html', {'object': topic, 'object_type': 'Topic'})

@login_required
def manage_subtopics(request, topic_id):
    """View to manage subtopics for a specific topic"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    topic = get_object_or_404(Topic, id=topic_id)
    subtopics = Subtopic.objects.filter(topic=topic).order_by('order')
    
    return render(request, 'admin/manage_subtopics.html', {'topic': topic, 'subtopics': subtopics})

@login_required
def create_subtopic(request, topic_id):
    """View to create a new subtopic for a specific topic"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    topic = get_object_or_404(Topic, id=topic_id)
    
    if request.method == 'POST':
        form = SubtopicForm(request.POST)
        if form.is_valid():
            subtopic = form.save(commit=False)
            subtopic.topic = topic
            subtopic.save()
            messages.success(request, 'Subtopic created successfully.')
            return redirect('manage_subtopics', topic_id=topic.id)
    else:
        form = SubtopicForm(initial={'topic': topic})
    
    return render(request, 'admin/edit_subtopic.html', {'form': form, 'topic': topic, 'is_new': True})

@login_required
def edit_subtopic(request, subtopic_id):
    """View to edit an existing subtopic"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    subtopic = get_object_or_404(Subtopic, id=subtopic_id)
    
    if request.method == 'POST':
        form = SubtopicForm(request.POST, instance=subtopic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subtopic updated successfully.')
            return redirect('manage_subtopics', topic_id=subtopic.topic.id)
    else:
        form = SubtopicForm(instance=subtopic)
    
    return render(request, 'admin/edit_subtopic.html', {'form': form, 'subtopic': subtopic, 'topic': subtopic.topic, 'is_new': False})

@login_required
def delete_subtopic(request, subtopic_id):
    """View to delete a subtopic"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    subtopic = get_object_or_404(Subtopic, id=subtopic_id)
    topic_id = subtopic.topic.id
    
    if request.method == 'POST':
        subtopic.delete()
        messages.success(request, 'Subtopic deleted successfully.')
        return redirect('manage_subtopics', topic_id=topic_id)
    
    return render(request, 'admin/delete_confirmation.html', {'object': subtopic, 'object_type': 'Subtopic'})

@login_required
def manage_quizzes(request, subtopic_id):
    """View to manage quizzes for a specific subtopic"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    subtopic = get_object_or_404(Subtopic, id=subtopic_id)
    quizzes = Quiz.objects.filter(subtopic=subtopic)
    
    return render(request, 'admin/manage_quizzes.html', {'subtopic': subtopic, 'quizzes': quizzes})

@login_required
def create_quiz(request, subtopic_id):
    """View to create a new quiz for a specific subtopic"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    subtopic = get_object_or_404(Subtopic, id=subtopic_id)
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.subtopic = subtopic
            quiz.save()
            messages.success(request, 'Quiz created successfully. Now add questions to it.')
            return redirect('edit_quiz_questions', quiz_id=quiz.id)
    else:
        form = QuizForm(initial={'subtopic': subtopic})
    
    return render(request, 'admin/edit_quiz.html', {'form': form, 'subtopic': subtopic, 'is_new': True})

@login_required
def edit_quiz(request, quiz_id):
    """View to edit an existing quiz"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully.')
            return redirect('manage_quizzes', subtopic_id=quiz.subtopic.id)
    else:
        form = QuizForm(instance=quiz)
    
    return render(request, 'admin/edit_quiz.html', {'form': form, 'quiz': quiz, 'subtopic': quiz.subtopic, 'is_new': False})

@login_required
def delete_quiz(request, quiz_id):
    """View to delete a quiz"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    subtopic_id = quiz.subtopic.id
    
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz deleted successfully.')
        return redirect('manage_quizzes', subtopic_id=subtopic_id)
    
    return render(request, 'admin/delete_confirmation.html', {'object': quiz, 'object_type': 'Quiz'})

@login_required
def edit_quiz_questions(request, quiz_id):
    """View to edit questions for a specific quiz"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if request.method == 'POST':
        question_formset = QuestionFormSet(request.POST, instance=quiz)
        if question_formset.is_valid():
            questions = question_formset.save(commit=False)
            
            # First save all questions
            for question in questions:
                question.save()
            
            # Delete questions that were marked for deletion
            for obj in question_formset.deleted_objects:
                obj.delete()
            
            # For each new question, create exactly 4 empty choices
            for question in questions:
                # Check if this is a new question without choices
                if question.choices.count() == 0:
                    for i in range(4):
                        Choice.objects.create(
                            question=question,
                            text=f"Option {i+1}",
                            is_correct=True if i == 0 else False  # First choice is correct by default
                        )
            
            messages.success(request, 'Questions updated successfully. Remember to edit choices for each question.')
            return redirect('manage_quizzes', subtopic_id=quiz.subtopic.id)
    else:
        question_formset = QuestionFormSet(instance=quiz)
    
    return render(request, 'admin/edit_quiz_questions.html', {
        'quiz': quiz,
        'question_formset': question_formset,
    })

@login_required
def edit_question_choices(request, question_id):
    """View to edit choices for a specific question"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    question = get_object_or_404(Question, id=question_id)
    
    # Ensure this question has exactly 4 choices
    current_choices_count = question.choices.count()
    if current_choices_count < 4:
        # Add more choices to make it exactly 4
        for i in range(4 - current_choices_count):
            Choice.objects.create(
                question=question,
                text=f"Option {current_choices_count + i + 1}",
                is_correct=False
            )
        messages.info(request, f"Added {4 - current_choices_count} choices to make exactly 4 options.")
    elif current_choices_count > 4:
        # Remove excess choices - keep the correct one if it exists
        correct_choice = question.choices.filter(is_correct=True).first()
        # If no correct choice exists, then don't prioritize any choices
        if not correct_choice:
            # Delete excess choices
            excess_choices = question.choices.order_by('-id')[:(current_choices_count - 4)]
            for choice in excess_choices:
                choice.delete()
        else:
            # Keep the correct choice and delete excess non-correct choices
            excess_choices = question.choices.filter(is_correct=False).order_by('-id')[:(current_choices_count - 4)]
            for choice in excess_choices:
                choice.delete()
        messages.info(request, f"Removed {current_choices_count - 4} choices to make exactly 4 options.")
    
    if request.method == 'POST':
        formset = ChoiceFormSet(request.POST, instance=question)
        if formset.is_valid():
            # Check that exactly one choice is marked as correct
            correct_count = 0
            for form in formset:
                if form.cleaned_data.get('is_correct'):
                    correct_count += 1
            
            if correct_count != 1:
                messages.error(request, 'Exactly one choice must be marked as correct.')
            else:
                formset.save()
                messages.success(request, 'Choices updated successfully.')
                return redirect('edit_quiz_questions', quiz_id=question.quiz.id)
    else:
        formset = ChoiceFormSet(instance=question)
    
    return render(request, 'admin/edit_question_choices.html', {
        'question': question,
        'formset': formset,
    })

@login_required
def student_performance(request):
    """View to show student performance data for admin"""
    if not is_admin(request.user):
        return HttpResponseForbidden("Access Denied: Admin privileges required")
    
    # Get all learners
    learners = UserProfile.objects.filter(role='learner').select_related('user')
    
    # Get quiz stats
    quiz_stats = Quiz.objects.annotate(
        attempts_count=Count('attempts'),
        avg_score=Avg('attempts__percentage')
    )
    
    # Get detailed performance data for learners
    learner_performance = []
    for profile in learners:
        user = profile.user
        attempts = QuizAttempt.objects.filter(user=user)
        avg_score = attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
        total_attempts = attempts.count()
        passed_count = attempts.filter(passed=True).count()
        
        learner_performance.append({
            'user': user,
            'avg_score': avg_score,
            'total_attempts': total_attempts,
            'passed_count': passed_count,
            'pass_rate': (passed_count / total_attempts * 100) if total_attempts > 0 else 0
        })
    
    context = {
        'learner_performance': learner_performance,
        'quiz_stats': quiz_stats,
    }
    
    return render(request, 'admin/student_performance.html', context)

# Learner views
@login_required
def learner_dashboard(request):
    """Learner dashboard view"""
    if not is_learner(request.user):
        return HttpResponseForbidden("Access Denied: Learner privileges required")
    
    weeks = Week.objects.all().order_by('order')
    
    # Get progress data for the learner
    completed_subtopics = TopicProgress.objects.filter(
        user=request.user, 
        reviewed=True
    ).values_list('subtopic_id', flat=True)
    completed_subtopics_count = len(completed_subtopics)
    
    # Get all topics and subtopics for statistics
    topics = Topic.objects.all()
    total_topics_count = topics.count()
    subtopics = Subtopic.objects.all()
    total_subtopics = subtopics.count()
    
    # Calculate overall progress percentage
    overall_progress = 0
    if total_subtopics > 0:
        overall_progress = (completed_subtopics_count / total_subtopics) * 100
    
    # Count completed topics (a topic is completed when all its subtopics are completed)
    completed_topics_count = 0
    for topic in topics:
        topic_subtopics = topic.subtopics.all()
        if topic_subtopics.count() > 0:
            topic_completed_subtopics = [s.id for s in topic_subtopics if s.id in completed_subtopics]
            if len(topic_completed_subtopics) == topic_subtopics.count():
                completed_topics_count += 1
    
    # Calculate completed topics percentage
    completed_topics_percent = 0
    if total_topics_count > 0:
        completed_topics_percent = (completed_topics_count / total_topics_count) * 100
    
    # Get quiz attempts and statistics
    all_quiz_attempts = QuizAttempt.objects.filter(user=request.user)
    quiz_attempts_count = all_quiz_attempts.count()
    passed_quizzes_count = all_quiz_attempts.filter(passed=True).count()
    failed_quizzes_count = quiz_attempts_count - passed_quizzes_count
    
    # Get average and highest quiz scores
    avg_quiz_score = all_quiz_attempts.aggregate(avg=Avg('percentage'))['avg'] if quiz_attempts_count > 0 else None
    highest_quiz_score = all_quiz_attempts.aggregate(max=Max('percentage'))['max'] if quiz_attempts_count > 0 else None
    
    # Get quiz attempts by week for the week progress display
    attempts_by_week = {}
    for week in weeks:
        topic_ids = Topic.objects.filter(week=week).values_list('id', flat=True)
        subtopic_ids = Subtopic.objects.filter(topic_id__in=topic_ids).values_list('id', flat=True)
        quiz_ids = Quiz.objects.filter(subtopic_id__in=subtopic_ids).values_list('id', flat=True)
        
        week_quiz_attempts = QuizAttempt.objects.filter(
            user=request.user,
            quiz_id__in=quiz_ids
        )
        
        attempts_by_week[week.id] = {
            'total': week_quiz_attempts.count(),
            'passed': week_quiz_attempts.filter(passed=True).count()
        }
    
    # Generate recent activities (combine quiz attempts and topic progress)
    recent_activities = []
    
    # Add recent quiz attempts
    recent_quiz_attempts = QuizAttempt.objects.filter(
        user=request.user
    ).select_related('quiz', 'quiz__subtopic').order_by('-completed_at')[:5]
    
    for attempt in recent_quiz_attempts:
        recent_activities.append({
            'type': 'quiz_attempt',
            'title': f"Quiz: {attempt.quiz.title}",
            'description': f"From {attempt.quiz.subtopic.title}",
            'timestamp': attempt.completed_at,
            'score': attempt.percentage,
            'passed': attempt.passed,
            'link': reverse('quiz_results', args=[attempt.id])
        })
    
    # Add recent topic progress
    recent_progress = TopicProgress.objects.filter(
        user=request.user, 
        reviewed=True
    ).select_related('subtopic', 'subtopic__topic').order_by('-reviewed_at')[:5]
    
    for progress in recent_progress:
        recent_activities.append({
            'type': 'topic_progress',
            'title': f"Completed: {progress.subtopic.title}",
            'description': f"In {progress.subtopic.topic.title}",
            'timestamp': progress.reviewed_at
        })
    
    # Sort all activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:5]  # Limit to 5 most recent
    
    # Generate recommended content
    recommended_content = []
    
    # Recommendation 1: Next uncompleted subtopic in the current week
    current_week = weeks.first()  # Default to first week
    
    # Try to find the most recent week with activity
    for week in weeks:
        topic_ids = Topic.objects.filter(week=week).values_list('id', flat=True)
        subtopic_ids = Subtopic.objects.filter(topic_id__in=topic_ids).values_list('id', flat=True)
        has_activity = TopicProgress.objects.filter(
            user=request.user,
            subtopic_id__in=subtopic_ids,
            reviewed=True
        ).exists()
        
        if has_activity:
            current_week = week
            break
    
    # Find uncompleted subtopics in the current week
    if current_week:
        topics_in_current_week = Topic.objects.filter(week=current_week).order_by('order')
        for topic in topics_in_current_week:
            uncompleted_subtopics = topic.subtopics.exclude(id__in=completed_subtopics).order_by('order')
            if uncompleted_subtopics.exists():
                next_subtopic = uncompleted_subtopics.first()
                recommended_content.append({
                    'type': 'subtopic',
                    'title': next_subtopic.title,
                    'description': f"Continue learning in {topic.title}",
                    'link': reverse('subtopic_detail', args=[next_subtopic.id]),
                    'context': f"Week {current_week.order}"
                })
                break
    
    # Recommendation 2: Retry failed quizzes
    failed_attempts = QuizAttempt.objects.filter(
        user=request.user, 
        passed=False
    ).select_related('quiz', 'quiz__subtopic').order_by('-completed_at')
    
    # Get a list of quiz IDs that have already been passed successfully
    passed_quiz_ids = QuizAttempt.objects.filter(
        user=request.user, 
        passed=True
    ).values_list('quiz_id', flat=True)
    
    # Filter to only show failed quizzes that haven't been subsequently passed
    failed_attempts = failed_attempts.exclude(quiz_id__in=passed_quiz_ids)
    
    if failed_attempts.exists():
        failed_attempt = failed_attempts.first()
        recommended_content.append({
            'type': 'failed_quiz',
            'title': f"Retry: {failed_attempt.quiz.title}",
            'description': f"Previous score: {failed_attempt.percentage:.1f}%",
            'link': reverse('take_quiz', args=[failed_attempt.quiz.id]),
            'context': "Retry"
        })
    
    # Recommendation 3: Take a quiz for a completed subtopic that hasn't been quizzed yet
    completed_subtopic_ids = list(completed_subtopics)
    if completed_subtopic_ids:
        completed_subtopics_with_quiz = Subtopic.objects.filter(
            id__in=completed_subtopic_ids,
            quizzes__isnull=False
        ).select_related('topic', 'topic__week').distinct()
        
        for subtopic in completed_subtopics_with_quiz:
            quiz = subtopic.quizzes.first()
            if quiz:
                has_attempted = QuizAttempt.objects.filter(
                    user=request.user,
                    quiz=quiz
                ).exists()
                
                if not has_attempted:
                    recommended_content.append({
                        'type': 'quiz',
                        'title': f"Take Quiz: {quiz.title}",
                        'description': f"For {subtopic.title}",
                        'link': reverse('take_quiz', args=[quiz.id]),
                        'context': f"Week {subtopic.topic.week.order}"
                    })
                    break
    
    # Limit to 3 recommendations
    recommended_content = recommended_content[:3]
    
    context = {
        # Basic data
        'weeks': weeks,
        'completed_subtopics': completed_subtopics,
        'attempts_by_week': attempts_by_week,
        
        # Statistics
        'total_subtopics': total_subtopics,
        'completed_subtopics_count': completed_subtopics_count,
        'overall_progress': overall_progress,
        'total_topics_count': total_topics_count,
        'completed_topics_count': completed_topics_count,
        'completed_topics_percent': completed_topics_percent,
        'quiz_attempts_count': quiz_attempts_count,
        'passed_quizzes_count': passed_quizzes_count,
        'failed_quizzes_count': failed_quizzes_count,
        'avg_quiz_score': avg_quiz_score,
        'highest_quiz_score': highest_quiz_score,
        
        # Activity and recommendations
        'recent_activities': recent_activities,
        'recommended_content': recommended_content,
    }
    
    return render(request, 'learner/dashboard.html', context)

@login_required
def week_detail(request, week_id):
    """View to show week details for learner"""
    if not is_learner(request.user):
        return HttpResponseForbidden("Access Denied: Learner privileges required")
    
    week = get_object_or_404(Week, id=week_id)
    topics = Topic.objects.filter(week=week).order_by('order')
    
    # Get subtopics for each topic
    topics_with_subtopics = []
    for topic in topics:
        subtopics = Subtopic.objects.filter(topic=topic).order_by('order')
        topics_with_subtopics.append({
            'topic': topic,
            'subtopics': subtopics
        })
    
    context = {
        'week': week,
        'topics_with_subtopics': topics_with_subtopics,
    }
    
    return render(request, 'learner/week_detail.html', context)

@login_required
def subtopic_detail(request, subtopic_id):
    """View to show subtopic details for learner"""
    if not is_learner(request.user):
        return HttpResponseForbidden("Access Denied: Learner privileges required")
    
    subtopic = get_object_or_404(Subtopic, id=subtopic_id)
    
    # Mark subtopic as reviewed
    progress, created = TopicProgress.objects.get_or_create(
        user=request.user,
        subtopic=subtopic,
        defaults={'reviewed': True, 'reviewed_at': timezone.now()}
    )
    
    if not progress.reviewed:
        progress.reviewed = True
        progress.reviewed_at = timezone.now()
        progress.save()
    
    # Get quizzes for this subtopic
    quizzes = Quiz.objects.filter(subtopic=subtopic)
    
    # Get quiz attempts for this user
    quiz_attempts = {}
    for quiz in quizzes:
        attempts = QuizAttempt.objects.filter(user=request.user, quiz=quiz)
        if attempts.exists():
            best_attempt = attempts.order_by('-percentage').first()
            quiz_attempts[quiz.id] = best_attempt
    
    context = {
        'subtopic': subtopic,
        'quizzes': quizzes,
        'quiz_attempts': quiz_attempts,
    }
    
    return render(request, 'learner/subtopic_detail.html', context)

@login_required
def take_quiz(request, quiz_id):
    """View to take a quiz"""
    if not is_learner(request.user):
        return HttpResponseForbidden("Access Denied: Learner privileges required")
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if subtopic has been reviewed
    try:
        progress = TopicProgress.objects.get(user=request.user, subtopic=quiz.subtopic)
        if not progress.reviewed:
            messages.warning(request, 'You need to review the subtopic before taking the quiz.')
            return redirect('subtopic_detail', subtopic_id=quiz.subtopic.id)
    except TopicProgress.DoesNotExist:
        messages.warning(request, 'You need to review the subtopic before taking the quiz.')
        return redirect('subtopic_detail', subtopic_id=quiz.subtopic.id)
    
    if request.method == 'POST':
        form = QuizResponseForm(request.POST, quiz=quiz)
        if form.is_valid():
            # Create a new quiz attempt
            quiz_attempt = QuizAttempt.objects.create(
                user=request.user,
                quiz=quiz,
                started_at=timezone.now(),
                completed_at=timezone.now()
            )
            
            # Process responses
            score = 0
            max_score = quiz.questions.count()
            
            for question in quiz.questions.all():
                selected_choice_id = form.cleaned_data.get(f'question_{question.id}')
                selected_choice = Choice.objects.get(id=selected_choice_id)
                is_correct = selected_choice.is_correct
                
                # Create response
                QuizResponse.objects.create(
                    quiz_attempt=quiz_attempt,
                    question=question,
                    selected_choice=selected_choice,
                    is_correct=is_correct
                )
                
                if is_correct:
                    score += 1
            
            # Update the quiz attempt with the score
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            passed = percentage >= quiz.passing_score
            
            quiz_attempt.score = score
            quiz_attempt.max_score = max_score
            quiz_attempt.percentage = percentage
            quiz_attempt.passed = passed
            quiz_attempt.save()
            
            return redirect('quiz_results', attempt_id=quiz_attempt.id)
    else:
        form = QuizResponseForm(quiz=quiz)
    
    context = {
        'quiz': quiz,
        'form': form,
        'time_limit_minutes': quiz.time_limit,
    }
    
    return render(request, 'learner/quiz.html', context)

@login_required
def quiz_results(request, attempt_id):
    """View to show quiz results"""
    if not is_learner(request.user):
        return HttpResponseForbidden("Access Denied: Learner privileges required")
    
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    # Get all responses with questions and choices
    responses = QuizResponse.objects.filter(quiz_attempt=attempt).select_related(
        'question', 'selected_choice'
    )
    
    # Organize responses by question
    question_responses = []
    for response in responses:
        # Get all choices for this question
        all_choices = Choice.objects.filter(question=response.question)
        correct_choice = Choice.objects.get(question=response.question, is_correct=True)
        
        question_responses.append({
            'question': response.question,
            'selected_choice': response.selected_choice,
            'is_correct': response.is_correct,
            'all_choices': all_choices,
            'correct_choice': correct_choice,
        })
    
    context = {
        'attempt': attempt,
        'question_responses': question_responses,
    }
    
    return render(request, 'learner/quiz_results.html', context)
