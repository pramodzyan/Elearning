from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Extension of User model to add role information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    ROLE_CHOICES = [
        ('learner', 'Learner'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='learner')
    
    def __str__(self):
        return f'{self.user.username} - {self.role}'

class Week(models.Model):
    """Weekly module in the course"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title
    
class Topic(models.Model):
    """Topic within a week"""
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f'{self.week.title} - {self.title}'

class Subtopic(models.Model):
    """Subtopic within a topic"""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='subtopics')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    youtube_link = models.URLField(blank=True, null=True)
    references = models.TextField(blank=True, null=True, help_text='Links to articles or documents related to this subtopic')
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f'{self.topic.title} - {self.title}'

class Quiz(models.Model):
    """Quiz for a subtopic"""
    subtopic = models.ForeignKey(Subtopic, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    time_limit = models.PositiveIntegerField(default=10, help_text='Time limit in minutes')
    passing_score = models.PositiveIntegerField(default=70, help_text='Passing score in percentage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'Quiz: {self.title} - {self.subtopic.title}'

class Question(models.Model):
    """Question in a quiz"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f'Question {self.order}: {self.text[:30]}...'

class Choice(models.Model):
    """Possible answer choice for a question"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.text} - {self.is_correct}'

class QuizAttempt(models.Model):
    """Record of a user's quiz attempt"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField(default=0)
    max_score = models.FloatField(default=0)
    percentage = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.quiz.title} - {self.percentage}%'

class QuizResponse(models.Model):
    """User's response to a quiz question"""
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f'Response: {self.question.text[:20]}... - {self.selected_choice.text[:20]}...'

class TopicProgress(models.Model):
    """Tracking whether a learner has reviewed a subtopic"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    subtopic = models.ForeignKey(Subtopic, on_delete=models.CASCADE)
    reviewed = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'subtopic']
    
    def __str__(self):
        return f'{self.user.username} - {self.subtopic.title} - {"Reviewed" if self.reviewed else "Not Reviewed"}'
