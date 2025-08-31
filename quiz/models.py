
# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Chapter(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="chapters")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.subject.name} - {self.name}"

class Question(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    image = models.ImageField(upload_to="questions/", blank=True, null=True)

    def __str__(self):
        return f"{self.chapter} - {self.text[:50]}"


class Question(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField(blank=True)                         # text may be blank if only image
    image = models.ImageField(upload_to="questions/", blank=True, null=True)

    def __str__(self):
        return self.text[:50] if self.text else f"Image Q ({self.id})"


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255, blank=True, null=True)   # can be image-only
    image = models.ImageField(upload_to="options/", blank=True, null=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text or f"Option #{self.id} (img)"

class QuizAttempt(models.Model):
    """
    One attempt per student per time they take a chapter quiz.
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    total_questions = models.PositiveIntegerField(default=0)
    attempted = models.PositiveIntegerField(default=0)
    correct = models.PositiveIntegerField(default=0)
    wrong = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        status = "DONE" if self.completed_at else "IN PROGRESS"
        return f"{self.student} | {self.chapter} | {status}"


class StudentAnswer(models.Model):
    """
    Stores per-question response within an attempt.
    """
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"{self.attempt.student} → Q{self.question_id}"