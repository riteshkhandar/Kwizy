from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.quiz import quiz_bp
from app.models import db, Quiz, Question, Option, Attempt, Answer
from app.forms import QuizForm
from flask_wtf import FlaskForm
from datetime import datetime

@quiz_bp.route('/')
def home():
    return redirect(url_for('auth.login'))

@quiz_bp.route('/dashboard')
@login_required
def dashboard():
    created = Quiz.query.filter_by(creator_id=current_user.id).all()
    attempted = Attempt.query.filter_by(user_id=current_user.id).all()
    return render_template('quiz/dashboard.html', quizzes=created, attempts=attempted)

@quiz_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    form = QuizForm()
    if request.method == 'POST' and form.validate_on_submit():
        questions = request.form.getlist('question_text[]')
        if not questions:
            flash('Please add at least one question.', 'danger')
            return render_template('quiz/create.html', form=form)
        quiz = Quiz(
            title=form.title.data,
            description=form.description.data,
            time_limit=form.time_limit.data or 0,
            user_limit=form.user_limit.data or 0,
            creator_id=current_user.id
        )
        db.session.add(quiz)
        db.session.flush()
        for i, q_text in enumerate(questions, start=1):
            question = Question(text=q_text, quiz_id=quiz.id, order=i)
            db.session.add(question)
            db.session.flush()
            options = request.form.getlist(f'option_{i}[]')
            correct = request.form.get(f'correct_{i}')
            for j, opt_text in enumerate(options, start=1):
                option = Option(
                    text=opt_text,
                    question_id=question.id,
                    is_correct=(str(j) == correct)
                )
                db.session.add(option)
        db.session.commit()
        flash('Quiz created successfully!', 'success')
        return redirect(url_for('quiz.dashboard'))
    return render_template('quiz/create.html', form=form)

@quiz_bp.route('/quiz/<code>')
@login_required
def quiz_detail(code):
    quiz = Quiz.query.filter_by(code=code).first_or_404()
    return render_template('quiz/detail.html', quiz=quiz)

@quiz_bp.route('/quiz/<code>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(code):
    quiz = Quiz.query.filter_by(code=code).first_or_404()
    if quiz.creator_id != current_user.id:
        flash('You are not allowed to edit this quiz.', 'danger')
        return redirect(url_for('quiz.dashboard'))

    form = QuizForm(obj=quiz)

    if request.method == 'POST' and form.validate_on_submit():
        quiz.title       = form.title.data
        quiz.description = form.description.data
        quiz.time_limit  = form.time_limit.data or 0
        quiz.user_limit  = form.user_limit.data or 0

        for q in quiz.questions:
            db.session.delete(q)
        db.session.flush()

        questions = request.form.getlist('question_text[]')
        if not questions:
            flash('Please add at least one question.', 'danger')
            return render_template('quiz/edit.html', form=form, quiz=quiz)

        for i, q_text in enumerate(questions, start=1):
            question = Question(text=q_text, quiz_id=quiz.id, order=i)
            db.session.add(question)
            db.session.flush()
            options = request.form.getlist(f'option_{i}[]')
            correct = request.form.get(f'correct_{i}')
            for j, opt_text in enumerate(options, start=1):
                option = Option(
                    text=opt_text,
                    question_id=question.id,
                    is_correct=(str(j) == correct)
                )
                db.session.add(option)

        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('quiz.quiz_detail', code=quiz.code))

    return render_template('quiz/edit.html', form=form, quiz=quiz)

@quiz_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join_quiz():
    form = FlaskForm()
    if request.method == 'POST' and form.validate_on_submit():
        code = request.form.get('code', '').strip().upper()
        quiz = Quiz.query.filter_by(code=code).first()
        if not quiz:
            flash('Invalid quiz code.', 'danger')
            return redirect(url_for('quiz.join_quiz'))
        return redirect(url_for('quiz.take_quiz', code=code))
    return render_template('quiz/join.html', form=form)

@quiz_bp.route('/take/<code>', methods=['GET'])
@login_required
def take_quiz(code):
    quiz = Quiz.query.filter_by(code=code).first_or_404()
    if not quiz.is_active:
        flash('This quiz is no longer active.', 'danger')
        return redirect(url_for('quiz.dashboard'))
    existing = Attempt.query.filter_by(quiz_id=quiz.id, user_id=current_user.id).first()
    if existing:
        flash('You have already attempted this quiz.', 'warning')
        return redirect(url_for('quiz.dashboard'))
    if quiz.user_limit and len(quiz.attempts) >= quiz.user_limit:
        flash('This quiz has reached its maximum number of participants.', 'danger')
        return redirect(url_for('quiz.dashboard'))
    form = FlaskForm()
    return render_template('quiz/take.html', quiz=quiz, form=form)

@quiz_bp.route('/take/<code>/start', methods=['POST'])
@login_required
def start_quiz(code):
    quiz = Quiz.query.filter_by(code=code).first_or_404()
    existing = Attempt.query.filter_by(quiz_id=quiz.id, user_id=current_user.id).first()
    if existing:
        return jsonify({'status': 'already_attempted'}), 400
    attempt = Attempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        total=len(quiz.questions)
    )
    db.session.add(attempt)
    db.session.commit()
    return jsonify({'status': 'ok', 'attempt_id': attempt.id})

@quiz_bp.route('/take/<code>/submit', methods=['POST'])
@login_required
def submit_quiz(code):
    quiz = Quiz.query.filter_by(code=code).first_or_404()
    attempt = Attempt.query.filter_by(
        quiz_id=quiz.id,
        user_id=current_user.id,
        finished_at=None
    ).first()
    if not attempt:
        flash('Invalid attempt or already submitted.', 'danger')
        return redirect(url_for('quiz.dashboard'))
    if quiz.time_limit:
        elapsed = (datetime.utcnow() - attempt.started_at).total_seconds() / 60
        if elapsed > quiz.time_limit + 0.5:
            db.session.delete(attempt)
            db.session.commit()
            flash('Time expired! Your attempt was not recorded.', 'danger')
            return redirect(url_for('quiz.dashboard'))
    score = 0
    for question in quiz.questions:
        selected_id = request.form.get(f'question_{question.id}')
        selected_id = int(selected_id) if selected_id else None
        option = Option.query.get(selected_id) if selected_id else None
        correct = option.is_correct if option else False
        if correct:
            score += 1
        answer = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_id=selected_id,
            is_correct=correct
        )
        db.session.add(answer)
    attempt.score = score
    attempt.finished_at = datetime.utcnow()
    db.session.commit()
    rank = Attempt.query.filter(
        Attempt.quiz_id == quiz.id,
        Attempt.score > score
    ).count() + 1
    total_attempts = Attempt.query.filter_by(quiz_id=quiz.id).count()
    return render_template('quiz/result.html', quiz=quiz, attempt=attempt, rank=rank, total_attempts=total_attempts)

@quiz_bp.route('/quiz/<code>/delete', methods=['POST'])
@login_required
def delete_quiz(code):
    quiz = Quiz.query.filter_by(code=code).first_or_404()
    if quiz.creator_id != current_user.id:
        flash('You are not allowed to delete this quiz.', 'danger')
        return redirect(url_for('quiz.dashboard'))
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully.', 'success')
    return redirect(url_for('quiz.dashboard'))