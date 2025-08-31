from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.utils import timezone
from django.http import Http404
from django.contrib.auth.hashers import make_password
from .models import User, Subject, Chapter, Question, Option, QuizAttempt, StudentAnswer
from django.http import JsonResponse

# Create your views here.
def home(request):
    return render(request, 'home.html')

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            # messages.success(request, f"Welcome back, {user.username}!")
            return redirect("student_dashboard")
        else:
            messages.error(request, "Invalid email or password. Please try again.")

    return render(request, "login.html")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password1")
        confirm_password = request.POST.get("password2")

        if not username or not email or not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return redirect("register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect("register")

        user = User(
            username=username,
            email=email,
            is_student=True,
            password=make_password(password)  # hash the password
        )
        user.save()

        messages.success(request, "Registration successful! Please login.")
        return redirect("login")

    return render(request, "register.html")

@login_required
def student_dashboard(request):
    subjects = Subject.objects.all()
    return render(request, "student_dashboard.html", {"subjects": subjects})


def get_chapters(request, subject_id):
    chapters = Chapter.objects.filter(subject_id=subject_id).values("id", "name")
    return JsonResponse(list(chapters), safe=False)


def take_quiz(request, subject_id, chapter_id):
    subject = Subject.objects.get(id=subject_id)
    chapter = Chapter.objects.get(id=chapter_id)
    return render(request, "quiz_page.html", {"subject": subject, "chapter": chapter})



def logout(request):
   auth_logout(request)  
   return redirect('login')

def _get_questions(chapter):
    return list(chapter.questions.all().order_by("id"))

def _get_or_create_active_attempt(user, subject, chapter, request):
    """
    Keep attempt id in session to prevent mixing with other chapters.
    """
    session_key = f"attempt_ch_{chapter.id}"
    attempt_id = request.session.get(session_key)
    attempt = None
    if attempt_id:
        attempt = QuizAttempt.objects.filter(id=attempt_id, student=user, chapter=chapter, completed_at__isnull=True).first()

    if not attempt:
        attempt = QuizAttempt.objects.create(
            student=user,
            subject=subject,
            chapter=chapter,
            total_questions=chapter.questions.count(),
        )
        request.session[session_key] = attempt.id

    return attempt

@login_required
def quiz_start(request, subject_id, chapter_id):
    subject = get_object_or_404(Subject, id=subject_id)
    chapter = get_object_or_404(Chapter, id=chapter_id, subject=subject)
    _get_or_create_active_attempt(request.user, subject, chapter, request)
    # go to first question
    return redirect("quiz_question", subject_id=subject.id, chapter_id=chapter.id, q_no=1)

@login_required
def quiz_question(request, subject_id, chapter_id, q_no):
    subject = get_object_or_404(Subject, id=subject_id)
    chapter = get_object_or_404(Chapter, id=chapter_id, subject=subject)
    questions = _get_questions(chapter)
    total = len(questions)
    if total == 0:
        return render(request, "no_questions.html", {"subject": subject, "chapter": chapter})

    # clamp q_no
    if q_no < 1 or q_no > total:
        raise Http404("Question number out of range.")

    question = questions[q_no - 1]
    options = question.options.all()

    attempt = _get_or_create_active_attempt(request.user, subject, chapter, request)

    # existing answer (to pre-check radio)
    saved = StudentAnswer.objects.filter(attempt=attempt, question=question).first()

    if request.method == "POST":
        # Save selected option (if any)
        selected_option_id = request.POST.get("option")
        if selected_option_id:
            selected_option = get_object_or_404(Option, id=selected_option_id, question=question)
            StudentAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    "selected_option": selected_option,
                    "is_correct": selected_option.is_correct,
                },
            )
        # Navigate
        if "previous" in request.POST and q_no > 1:
            return redirect("quiz_question", subject_id=subject_id, chapter_id=chapter_id, q_no=q_no - 1)

        if "next" in request.POST and q_no < total:
            return redirect("quiz_question", subject_id=subject_id, chapter_id=chapter_id, q_no=q_no + 1)

        if "submit" in request.POST:
            # compute and finalize
            answers = StudentAnswer.objects.filter(attempt=attempt)
            attempted = answers.exclude(selected_option__isnull=True).count()
            correct = answers.filter(is_correct=True).count()
            wrong = max(0, attempted - correct)

            attempt.attempted = attempted
            attempt.correct = correct
            attempt.wrong = wrong
            attempt.completed_at = timezone.now()
            attempt.save()

            # clear session for this chapter
            session_key = f"attempt_ch_{chapter.id}"
            request.session.pop(session_key, None)

            return redirect("quiz_result", subject_id=subject_id, chapter_id=chapter_id, attempt_id=attempt.id)

    return render(
        request,
        "quiz.html",
        {
            "subject": subject,
            "chapter": chapter,
            "question": question,
            "options": options,
            "q_no": q_no,
            "total": total,
            "saved": saved,
        },
    )

@login_required
def quiz_result(request, subject_id, chapter_id, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    subject = attempt.subject
    chapter = attempt.chapter

    answers = []
    for ans in attempt.answers.select_related("question", "selected_option"):
        correct_option = ans.question.options.filter(is_correct=True).first()
        answers.append({
            "question": ans.question,
            "selected_option": ans.selected_option,
            "is_correct": ans.is_correct,
            "correct_option": correct_option,
        })

    context = {
        "attempt": attempt,
        "subject": subject,
        "chapter": chapter,
        "answers": answers,
    }
    return render(request, "result.html", context)
