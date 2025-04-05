from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Week, Topic, Subtopic, Quiz, Question, Choice

class UserRegistrationForm(UserCreationForm):
    """Form for user registration with role selection"""
    ROLE_CHOICES = [
        ('learner', 'Learner'),
        ('admin', 'Admin'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect, initial='learner')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

class WeekForm(forms.ModelForm):
    """Form for creating and editing Weeks"""
    class Meta:
        model = Week
        fields = ('title', 'description', 'order')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class TopicForm(forms.ModelForm):
    """Form for creating and editing Topics"""
    class Meta:
        model = Topic
        fields = ('week', 'title', 'description', 'order')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class SubtopicForm(forms.ModelForm):
    """Form for creating and editing Subtopics"""
    class Meta:
        model = Subtopic
        fields = ('topic', 'title', 'description', 'youtube_link', 'references', 'order')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'references': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter reference links or text here'}),
        }

class QuizForm(forms.ModelForm):
    """Form for creating and editing Quizzes"""
    class Meta:
        model = Quiz
        fields = ('subtopic', 'title', 'description', 'time_limit', 'passing_score')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class QuestionForm(forms.ModelForm):
    """Form for creating and editing Questions"""
    class Meta:
        model = Question
        fields = ('text', 'order')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
        }

class ChoiceForm(forms.ModelForm):
    """Form for creating and editing Choices"""
    class Meta:
        model = Choice
        fields = ('text', 'is_correct')

ChoiceFormSet = forms.inlineformset_factory(
    Question, 
    Choice,
    form=ChoiceForm,
    extra=4,
    max_num=4,
    min_num=4,
    validate_min=True,
    validate_max=True,
    can_delete=False,
    absolute_max=4  # Ensures exactly 4 choices, no more
)

QuestionFormSet = forms.inlineformset_factory(
    Quiz,
    Question,
    form=QuestionForm,
    extra=1,
    can_delete=True
)

class QuizResponseForm(forms.Form):
    """Form for submitting quiz responses"""
    def __init__(self, *args, **kwargs):
        quiz = kwargs.pop('quiz')
        super(QuizResponseForm, self).__init__(*args, **kwargs)
        
        for question in quiz.questions.all():
            # Ensure every question has exactly 4 choices
            current_choices = list(question.choices.all())
            choices_count = len(current_choices)
            
            # If not exactly 4 choices, fix it
            if choices_count != 4:
                # If fewer than 4, add more
                if choices_count < 4:
                    for i in range(4 - choices_count):
                        Choice.objects.create(
                            question=question,
                            text=f"Option {choices_count + i + 1}",
                            is_correct=False
                        )
                # If more than 4, remove extras (keeping the correct one if possible)
                elif choices_count > 4:
                    # Try to keep the correct choice
                    correct_choice = next((c for c in current_choices if c.is_correct), None)
                    keep_ids = []
                    
                    if correct_choice:
                        keep_ids.append(correct_choice.id)
                        # Keep 3 more non-correct choices
                        non_correct = [c for c in current_choices if not c.is_correct]
                        for c in non_correct[:3]:
                            keep_ids.append(c.id)
                    else:
                        # No correct choice, just keep first 4
                        for c in current_choices[:4]:
                            keep_ids.append(c.id)
                    
                    # Delete all choices not in keep_ids
                    Choice.objects.filter(question=question).exclude(id__in=keep_ids).delete()
                
                # Refresh the choices
                current_choices = list(question.choices.all())
            
            # Make sure there's a correct choice
            if not any(choice.is_correct for choice in current_choices):
                current_choices[0].is_correct = True
                current_choices[0].save()
            
            # Now create the form field
            choices = [(choice.id, choice.text) for choice in current_choices]
            self.fields[f'question_{question.id}'] = forms.ChoiceField(
                label=question.text,
                choices=choices,
                widget=forms.RadioSelect
            )
