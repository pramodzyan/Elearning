from django.contrib import admin
from .models import (
    UserProfile, Week, Topic, Subtopic, 
    Quiz, Question, Choice, 
    QuizAttempt, QuizResponse, TopicProgress
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1

@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)
    inlines = [TopicInline]

class SubtopicInline(admin.TabularInline):
    model = Subtopic
    extra = 1

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'week', 'order', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    list_filter = ('week', 'created_at')
    inlines = [SubtopicInline]

class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 0

@admin.register(Subtopic)
class SubtopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'order', 'youtube_link', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    list_filter = ('topic__week', 'topic', 'created_at')
    inlines = [QuizInline]

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    min_num = 4
    max_num = 4
    validate_min = True
    validate_max = True
    can_delete = False

    def get_formset(self, request, obj=None, **kwargs):
        """Override formset factory to enforce exactly 4 choices"""
        formset = super().get_formset(request, obj, **kwargs)
        return formset

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtopic', 'time_limit', 'passing_score', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('subtopic__topic__week', 'subtopic__topic', 'subtopic')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text', 'order')
    search_fields = ('text',)
    list_filter = ('quiz',)
    inlines = [ChoiceInline]
    
    def save_model(self, request, obj, form, change):
        """Ensure each question has exactly 4 choices"""
        super().save_model(request, obj, form, change)
        
        # After saving, check if this question has exactly 4 choices
        current_choices_count = obj.choices.count()
        if current_choices_count < 4:
            # Add more choices to make it exactly 4
            for i in range(4 - current_choices_count):
                Choice.objects.create(
                    question=obj,
                    text=f"Option {current_choices_count + i + 1}",
                    is_correct=True if i == 0 and current_choices_count == 0 else False
                )
        elif current_choices_count > 4:
            # Keep only 4 choices (prioritizing the correct one if it exists)
            correct_choice = obj.choices.filter(is_correct=True).first()
            if correct_choice:
                # Keep the correct choice and 3 more non-correct choices
                non_correct_choices = obj.choices.filter(is_correct=False).order_by('id')[:3]
                keep_ids = [correct_choice.id] + [c.id for c in non_correct_choices]
                obj.choices.exclude(id__in=keep_ids).delete()
            else:
                # Just keep the first 4 choices
                keep_ids = obj.choices.all().order_by('id')[:4].values_list('id', flat=True)
                obj.choices.exclude(id__in=keep_ids).delete()
                
        # Make sure at least one choice is marked correct
        if not obj.choices.filter(is_correct=True).exists():
            first_choice = obj.choices.first()
            if first_choice:
                first_choice.is_correct = True
                first_choice.save()

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    search_fields = ('text',)
    list_filter = ('question__quiz', 'is_correct')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'max_score', 'percentage', 'passed', 'started_at', 'completed_at')
    search_fields = ('user__username', 'quiz__title')
    list_filter = ('quiz__subtopic__topic__week', 'quiz__subtopic__topic', 'passed')

@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ('quiz_attempt', 'question', 'selected_choice', 'is_correct')
    search_fields = ('question__text', 'selected_choice__text')
    list_filter = ('is_correct', 'quiz_attempt__quiz')

@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'subtopic', 'reviewed', 'reviewed_at')
    search_fields = ('user__username', 'subtopic__title')
    list_filter = ('reviewed', 'subtopic__topic__week', 'subtopic__topic')
