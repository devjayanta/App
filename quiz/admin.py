from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subject, Chapter, Question, Option, QuizAttempt, StudentAnswer

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("username", "email", "is_teacher", "is_student", "is_staff")

admin.site.register(User, CustomUserAdmin)


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    inlines = [ChapterInline]

class OptionInline(admin.TabularInline):
    model = Option
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "chapter", "short_text")
    list_filter = ("chapter__subject", "chapter")
    inlines = [OptionInline]

    def short_text(self, obj):
        return (obj.text or "")[:60]

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "subject")
    list_filter = ("subject",)
    search_fields = ("name", "subject__name")

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "subject", "chapter", "correct", "wrong", "attempted", "total_questions", "completed_at")
    list_filter = ("subject", "chapter", "completed_at")
    search_fields = ("student__username", "student__email", "chapter__name")

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt", "question", "selected_option", "is_correct")
    list_filter = ("is_correct", "attempt__chapter__subject", "attempt__chapter")