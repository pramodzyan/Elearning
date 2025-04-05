from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import (
    UserProfile, Week, Topic, Subtopic, 
    Quiz, Question, Choice, QuizAttempt
)

class UserRegistrationTest(TestCase):
    """Tests for user registration functionality"""
    
    def test_register_learner(self):
        """Test registering a new learner"""
        response = self.client.post(reverse('register'), {
            'username': 'learner1',
            'email': 'learner1@example.com',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'role': 'learner'
        })
        
        # Check user is created
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.username, 'learner1')
        
        # Check profile is created with correct role
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.role, 'learner')
        
        # Check redirect to learner dashboard
        self.assertRedirects(response, reverse('learner_dashboard'))
    
    def test_register_admin(self):
        """Test registering a new admin"""
        response = self.client.post(reverse('register'), {
            'username': 'admin1',
            'email': 'admin1@example.com',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'role': 'admin'
        })
        
        # Check user is created
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.username, 'admin1')
        
        # Check profile is created with correct role
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.role, 'admin')
        
        # Check redirect to admin dashboard
        self.assertRedirects(response, reverse('admin_dashboard'))

class WeekManagementTest(TestCase):
    """Tests for week management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass'
        )
        UserProfile.objects.create(user=self.admin_user, role='admin')
        
        # Create learner user
        self.learner_user = User.objects.create_user(
            username='learner',
            password='learnerpass'
        )
        UserProfile.objects.create(user=self.learner_user, role='learner')
        
        # Create test week
        self.week = Week.objects.create(
            title='Test Week',
            description='Test Description',
            order=1
        )
    
    def test_admin_can_view_manage_weeks(self):
        """Test admin can access week management page"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('manage_weeks'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Week')
    
    def test_learner_cannot_view_manage_weeks(self):
        """Test learner cannot access week management page"""
        self.client.login(username='learner', password='learnerpass')
        response = self.client.get(reverse('manage_weeks'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_admin_can_create_week(self):
        """Test admin can create a new week"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('create_week'), {
            'title': 'New Week',
            'description': 'New Description',
            'order': 2
        })
        self.assertRedirects(response, reverse('manage_weeks'))
        self.assertEqual(Week.objects.count(), 2)
        new_week = Week.objects.get(title='New Week')
        self.assertEqual(new_week.description, 'New Description')
        self.assertEqual(new_week.order, 2)

class QuizTest(TestCase):
    """Tests for quiz functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create learner user
        self.learner_user = User.objects.create_user(
            username='learner',
            password='learnerpass'
        )
        UserProfile.objects.create(user=self.learner_user, role='learner')
        
        # Create week, topic, subtopic
        self.week = Week.objects.create(
            title='Test Week',
            description='Test Description',
            order=1
        )
        self.topic = Topic.objects.create(
            week=self.week,
            title='Test Topic',
            description='Test Topic Description',
            order=1
        )
        self.subtopic = Subtopic.objects.create(
            topic=self.topic,
            title='Test Subtopic',
            description='Test Subtopic Description',
            youtube_link='https://www.youtube.com/watch?v=test',
            references='Test References',
            order=1
        )
        
        # Mark subtopic as reviewed
        TopicProgress.objects.create(
            user=self.learner_user,
            subtopic=self.subtopic,
            reviewed=True
        )
        
        # Create quiz with question and choices
        self.quiz = Quiz.objects.create(
            subtopic=self.subtopic,
            title='Test Quiz',
            description='Test Quiz Description',
            time_limit=10,
            passing_score=70
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            text='Test Question',
            order=1
        )
        
        # Create 4 choices with one correct
        self.choice1 = Choice.objects.create(
            question=self.question,
            text='Choice 1',
            is_correct=True
        )
        self.choice2 = Choice.objects.create(
            question=self.question,
            text='Choice 2',
            is_correct=False
        )
        self.choice3 = Choice.objects.create(
            question=self.question,
            text='Choice 3',
            is_correct=False
        )
        self.choice4 = Choice.objects.create(
            question=self.question,
            text='Choice 4',
            is_correct=False
        )
    
    def test_learner_can_take_quiz(self):
        """Test learner can take a quiz"""
        self.client.login(username='learner', password='learnerpass')
        response = self.client.get(reverse('take_quiz', args=[self.quiz.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Quiz')
        self.assertContains(response, 'Test Question')
    
    def test_quiz_submission_correct_answer(self):
        """Test quiz submission with correct answer"""
        self.client.login(username='learner', password='learnerpass')
        response = self.client.post(reverse('take_quiz', args=[self.quiz.id]), {
            f'question_{self.question.id}': str(self.choice1.id)  # Correct choice
        })
        
        # Should have created an attempt
        self.assertEqual(QuizAttempt.objects.count(), 1)
        attempt = QuizAttempt.objects.first()
        
        # Check attempt details
        self.assertEqual(attempt.user, self.learner_user)
        self.assertEqual(attempt.quiz, self.quiz)
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.max_score, 1)
        self.assertEqual(attempt.percentage, 100)
        self.assertTrue(attempt.passed)
        
        # Should redirect to results page
        self.assertRedirects(response, reverse('quiz_results', args=[attempt.id]))
    
    def test_quiz_submission_wrong_answer(self):
        """Test quiz submission with wrong answer"""
        self.client.login(username='learner', password='learnerpass')
        response = self.client.post(reverse('take_quiz', args=[self.quiz.id]), {
            f'question_{self.question.id}': str(self.choice2.id)  # Wrong choice
        })
        
        # Should have created an attempt
        self.assertEqual(QuizAttempt.objects.count(), 1)
        attempt = QuizAttempt.objects.first()
        
        # Check attempt details
        self.assertEqual(attempt.user, self.learner_user)
        self.assertEqual(attempt.quiz, self.quiz)
        self.assertEqual(attempt.score, 0)
        self.assertEqual(attempt.max_score, 1)
        self.assertEqual(attempt.percentage, 0)
        self.assertFalse(attempt.passed)
