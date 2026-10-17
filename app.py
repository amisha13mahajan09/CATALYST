import os
import re
import time
import json
import datetime
import decimal
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask.json.provider import DefaultJSONProvider
import db
import score_engine
import admin_analytics


class CatalystJSONProvider(DefaultJSONProvider):
    """Custom JSON provider that handles datetime and Decimal types from PostgreSQL."""
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)

app = Flask(__name__)
app.json_provider_class = CatalystJSONProvider
app.json = CatalystJSONProvider(app)
app.secret_key = os.environ.get('SECRET_KEY', 'catalyst_secret_key_2026_placement_platform')

# Register custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Parses a JSON string into a Python object (list/dict). Returns empty list on failure."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return []

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Run schema migrations and seed admin data on startup
db.ensure_pg_schema()
db.seed_pg_admins()
db.seed_from_app_sql()

def validate_and_save_file(file_storage, prefix, student_id):
    """
    Validates that the uploaded file is a genuine Image (PNG, JPG, GIF, WEBP) or PDF document.
    Inspects magic header bytes and file extensions. Returns saved relative path.
    Preserves the exact filename uploaded by the user.
    """
    if not file_storage or not file_storage.filename or file_storage.filename.strip() == '':
        return None

    orig_name = os.path.basename(file_storage.filename.replace('\\', '/')).strip()
    if not orig_name:
        return None

    filename_lower = orig_name.lower()
    allowed_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf')
    if not any(filename_lower.endswith(ext) for ext in allowed_exts):
        raise ValueError(f"Invalid file format for {prefix}! Only valid Images (PNG, JPG, GIF, WEBP) and PDF files are allowed.")

    header = file_storage.read(64)
    file_storage.seek(0)

    if len(header) < 4:
        raise ValueError("Uploaded file is corrupted or empty.")

    is_pdf = header.startswith(b'%PDF-')
    is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
    is_jpeg = header.startswith(b'\xff\xd8\xff')
    is_gif = header.startswith(b'GIF87a') or header.startswith(b'GIF89a')
    is_webp = header.startswith(b'RIFF') and b'WEBP' in header[:16]

    if not (is_pdf or is_png or is_jpeg or is_gif or is_webp):
        raise ValueError(f"Document verification failed for {prefix}: The uploaded file content is NOT a genuine image or PDF document.")

    # Sanitize illegal filesystem characters while keeping the exact uploaded name intact
    safe_name = re.sub(r'[/\\?%*:|"<>]', '_', orig_name).strip()
    if not safe_name:
        ext = os.path.splitext(filename_lower)[1]
        safe_name = f"document{ext}"

    # Save within a student & prefix scoped folder to avoid overwriting files with the same name across fields/students
    target_dir = os.path.join(UPLOAD_FOLDER, f"std_{student_id}", str(prefix))
    os.makedirs(target_dir, exist_ok=True)
    dest_path = os.path.join(target_dir, safe_name)
    file_storage.save(dest_path)
    return f"uploads/std_{student_id}/{prefix}/{safe_name}"

@app.context_processor
def inject_user():
    """Injects current session user info into all Jinja2 templates."""
    return dict(
        current_user={
            'id': session.get('user_id'),
            'name': session.get('full_name'),
            'prn': session.get('prn'),
            'role': session.get('role')
        }
    )

@app.route('/')
def home():
    """Landing Page route."""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student Registration Handler."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        prn = request.form.get('prn', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        college = request.form.get('college', '').strip()
        department_id = request.form.get('department_id', '')
        year_sem = request.form.get('year_sem', '')
        graduation_year = request.form.get('graduation_year', '')

        if not (full_name and username and email and prn and password and college and department_id and year_sem and graduation_year):
            flash('Please fill in all mandatory fields.', 'danger')
            return render_template('register.html', departments=db.get_departments(), form_data=request.form)

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'danger')
            return render_template('register.html', departments=db.get_departments(), form_data=request.form)

        try:
            parts = year_sem.split('_')
            current_year = parts[0]
            current_semester = int(parts[1])
        except Exception:
            flash('Invalid Current Year & Semester selection.', 'danger')
            return render_template('register.html', departments=db.get_departments(), form_data=request.form)

        success, result = db.register_student(
            prn=prn,
            full_name=full_name,
            email=email,
            raw_password=password,
            college=college,
            department_id=department_id,
            current_year=current_year,
            current_semester=current_semester,
            graduation_year=graduation_year,
            username=username
        )

        if success:
            student_id = result
            session['user_id'] = student_id
            session['prn'] = prn
            session['username'] = username
            session['full_name'] = full_name
            session['role'] = 'student'
            flash(f'Welcome aboard, {full_name}! Account created successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result, 'danger')
            return render_template('register.html', departments=db.get_departments(), form_data=request.form)

    departments = db.get_departments()
    return render_template('register.html', departments=departments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified Student and Admin/Faculty Login Handler."""
    if request.method == 'POST':
        login_type = request.form.get('login_type', 'student')
        identifier = (request.form.get('identifier') or request.form.get('prn') or request.form.get('username') or '').strip()
        password = request.form.get('password', '')

        if not (identifier and password):
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')

        if login_type == 'admin':
            # Admin-only authentication
            admin = db.authenticate_admin(identifier, password)
            if admin:
                session['user_id'] = admin['admin_id']
                session['username'] = admin['username']
                session['full_name'] = admin['full_name']
                session['role'] = admin['role']
                flash(f'Logged in successfully as {admin["role"]} ({admin["full_name"]}).', 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid admin username or password. Please check your credentials.', 'danger')
            return render_template('login.html')
        else:
            # Student authentication (by username or PRN)
            student = db.authenticate_student(identifier, password)
            if student:
                session['user_id'] = student['student_id']
                session['prn'] = student['prn']
                session['username'] = student.get('username', '')
                session['full_name'] = student['full_name']
                session['role'] = 'student'
                flash(f'Welcome back, {student["full_name"]}!', 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid username or password. Please check your credentials.', 'danger')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Unified Dashboard Page for Student & Admin."""
    if not session.get('user_id'):
        flash('Please login to access your placement dashboard.', 'warning')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    role = session.get('role', 'student')

    if role == 'student':
        student_data = db.get_student_by_id(user_id)
        if not student_data:
            session.clear()
            return redirect(url_for('login'))
        
        card_data = db.get_student_card_data(user_id)
        latest_assessment = db.get_latest_assessment(user_id)
        assessment_history = db.get_assessment_history(user_id)

        # Generate student analytics charts using Matplotlib & Seaborn
        student_charts = {}
        if latest_assessment:
            computed = score_engine.compute_placement_readiness(student_data, card_data)
            latest_assessment['total_score'] = computed['total_score']
            latest_assessment['classification'] = computed['classification']
            latest_assessment['category_scores'] = computed['category_scores']
            latest_assessment['ideal_comparison'] = computed['ideal_comparison']
            latest_assessment['skill_gaps'] = computed['skill_gaps']
            latest_assessment['recommendations'] = computed['recommendations']
            if latest_assessment.get('category_scores'):
                student_charts = admin_analytics.generate_student_seaborn_charts(
                    latest_assessment['category_scores'],
                    assessment_history
                )

        return render_template(
            'dashboard.html',
            student=student_data,
            card_data=card_data,
            latest_assessment=latest_assessment,
            assessment_history=assessment_history,
            student_charts=student_charts
        )
    else:
        # Admin / Faculty Dashboard View
        students_list = db.get_all_students_for_admin()
        departments = db.get_departments()
        admin_metrics = admin_analytics.compute_admin_metrics(students_list)
        admin_charts = admin_analytics.generate_admin_seaborn_charts(students_list)

        return render_template(
            'dashboard.html',
            admin_name=session.get('full_name'),
            role=role,
            students=students_list,
            departments=departments,
            admin_metrics=admin_metrics,
            admin_charts=admin_charts
        )

@app.route('/logout')
def logout():
    """Logs out user."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route('/api/save_card/<card_name>', methods=['POST'])
def save_card(card_name):
    """API endpoint to save student responses for any of the 13 dashboard cards."""
    if not session.get('user_id') or session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized request. Please log in.'}), 401

    student_id = session['user_id']
    student_record = db.get_student_by_id(student_id)
    current_sem = student_record['current_semester'] if student_record else 1

    try:
        if card_name == 'academics':
            perc_10 = request.form.get('percentage_10th')
            perc_12 = request.form.get('percentage_12th')
            if not (perc_10 and perc_12):
                return jsonify({'success': False, 'message': '10th and 12th Std percentages are mandatory.'}), 400

            sems_sgpa = {}
            for s in range(1, current_sem):
                val = request.form.get(f'semester_{s}_sgpa')
                if not val:
                    return jsonify({'success': False, 'message': f'Semester {s} SGPA is mandatory for your academic level.'}), 400
                sems_sgpa[s] = float(val)

            # Validate marksheet file uploads (or preserve existing)
            m10_path = validate_and_save_file(request.files.get('marksheet_10th'), '10th_marksheet', student_id)
            if not m10_path:
                m10_path = request.form.get('existing_marksheet_10th')

            m12_path = validate_and_save_file(request.files.get('marksheet_12th'), '12th_marksheet', student_id)
            if not m12_path:
                m12_path = request.form.get('existing_marksheet_12th')
            
            # Retrieve existing semester marksheets if available and merge
            existing_sems_json = request.form.get('existing_marksheet_sems_json')
            sems_files = {}
            if existing_sems_json:
                try:
                    sems_files = json.loads(existing_sems_json) if isinstance(existing_sems_json, str) else existing_sems_json
                except Exception:
                    sems_files = {}

            for s in range(1, current_sem):
                sf_path = validate_and_save_file(request.files.get(f'marksheet_sem_{s}'), f'sem_{s}_marksheet', student_id)
                if sf_path:
                    sems_files[str(s)] = sf_path
                elif request.form.get(f'existing_marksheet_sem_{s}'):
                    sems_files[str(s)] = request.form.get(f'existing_marksheet_sem_{s}')

            has_backlogs = request.form.get('previous_backlogs') == 'yes'
            backlogs_list = []
            if has_backlogs:
                levels = request.form.getlist('backlog_level[]')
                subjects = request.form.getlist('backlog_subject[]')
                for lvl, sbj in zip(levels, subjects):
                    if lvl and sbj and sbj.strip():
                        backlogs_list.append({'level': lvl, 'subject': sbj.strip()})

            db.save_academics_card(
                student_id=student_id,
                percentage_10th=float(perc_10),
                percentage_12th=float(perc_12),
                sems_sgpa_dict=sems_sgpa,
                previous_backlogs=has_backlogs,
                backlogs_list=backlogs_list,
                marksheet_10th_path=m10_path,
                marksheet_12th_path=m12_path,
                sems_marksheet_json=json.dumps(sems_files) if sems_files else None
            )

        elif card_name == 'coding_languages':
            languages = request.form.getlist('language_name[]')
            depths = request.form.getlist('proficiency_level[]')
            langs_list = []
            for lang, depth in zip(languages, depths):
                if lang:
                    langs_list.append({'language_name': lang, 'proficiency_level': depth})
            db.save_coding_languages_card(student_id, langs_list)

        elif card_name == 'technical_skills':
            skills = request.form.getlist('skill_name[]')
            depths = request.form.getlist('proficiency_level[]')
            skills_list = []
            if 'NONE' in [s.strip().upper() for s in skills]:
                skills_list = [{'skill_name': 'NONE', 'proficiency_level': 'Beginner'}]
            else:
                for sk, dp in zip(skills, depths):
                    if sk and sk.strip():
                        skills_list.append({'skill_name': sk.strip(), 'proficiency_level': dp})
            db.save_technical_skills_card(student_id, skills_list)

        elif card_name == 'coding_platforms':
            platforms = request.form.getlist('platform_name[]')
            urls = request.form.getlist('profile_url[]')
            questions = request.form.getlist('questions_solved[]')
            plist = []
            for p, u, q in zip(platforms, urls, questions):
                if p:
                    plist.append({'platform_name': p, 'profile_url': u, 'questions_solved': int(q) if q and q.isdigit() else 0})
            db.save_coding_platforms_card(student_id, plist)

        elif card_name == 'linkedin':
            uses_academic = request.form.get('uses_academic') == 'yes'
            url = request.form.get('profile_url', '').strip()
            posts = request.form.get('number_of_posts', '0')
            db.save_linkedin_card(student_id, uses_academic, url, int(posts) if posts.isdigit() else 0)

        elif card_name == 'research_papers':
            has_paper = request.form.get('has_published') == 'yes'
            papers_list = []
            if has_paper:
                titles = request.form.getlist('paper_title[]')
                pubs = request.form.getlist('publication_name[]')
                urls = request.form.getlist('paper_url[]')
                docs = request.files.getlist('paper_document[]')
                existing_docs = request.form.getlist('existing_paper_document[]')
                for idx, t in enumerate(titles):
                    if t and t.strip():
                        doc_file = docs[idx] if idx < len(docs) else None
                        doc_path = validate_and_save_file(doc_file, f'research_{idx}', student_id) if doc_file else ''
                        if not doc_path and idx < len(existing_docs):
                            doc_path = existing_docs[idx]
                        papers_list.append({
                            'paper_title': t.strip(),
                            'publication_name': pubs[idx] if idx < len(pubs) else '',
                            'paper_url': urls[idx] if idx < len(urls) else '',
                            'document_path': doc_path or ''
                        })
            db.save_research_papers_card(student_id, papers_list, has_published=has_paper)

        elif card_name == 'internships':
            has_internship = request.form.get('has_internship') == 'yes'
            internships_list = []
            if has_internship:
                companies = request.form.getlist('company_name[]')
                roles = request.form.getlist('role[]')
                starts = request.form.getlist('start_date[]')
                ends = request.form.getlist('end_date[]')
                letters = request.files.getlist('offer_letter[]')
                existing_letters = request.form.getlist('existing_offer_letter[]')
                for idx, comp in enumerate(companies):
                    if comp and comp.strip():
                        let_file = letters[idx] if idx < len(letters) else None
                        let_path = validate_and_save_file(let_file, f'internship_{idx}', student_id) if let_file else ''
                        if not let_path and idx < len(existing_letters):
                            let_path = existing_letters[idx]
                        internships_list.append({
                            'company_name': comp.strip(),
                            'role': roles[idx] if idx < len(roles) else '',
                            'start_date': starts[idx] if idx < len(starts) else '',
                            'end_date': ends[idx] if idx < len(ends) else '',
                            'offer_letter_path': let_path or ''
                        })
            db.save_internships_card(student_id, internships_list, has_internship=has_internship)

        elif card_name == 'hackathons':
            has_hackathon = request.form.get('has_hackathon') == 'yes'
            hackathons_list = []
            if has_hackathon:
                names = request.form.getlist('hackathon_name[]')
                organizers = request.form.getlist('organizer[]')
                positions = request.form.getlist('position[]')
                certs = request.files.getlist('certificate[]')
                existing_certs = request.form.getlist('existing_hackathon_certificate[]')
                for idx, hname in enumerate(names):
                    if hname and hname.strip():
                        cert_file = certs[idx] if idx < len(certs) else None
                        cert_path = validate_and_save_file(cert_file, f'hackathon_{idx}', student_id) if cert_file else ''
                        if not cert_path and idx < len(existing_certs):
                            cert_path = existing_certs[idx]
                        hackathons_list.append({
                            'hackathon_name': hname.strip(),
                            'organizer': organizers[idx] if idx < len(organizers) else '',
                            'position': positions[idx] if idx < len(positions) else '',
                            'certificate_path': cert_path or ''
                        })
            db.save_hackathons_card(student_id, hackathons_list, has_hackathon=has_hackathon)

        elif card_name == 'courses_certificates':
            has_cert = request.form.get('has_certificate') == 'yes'
            certs_list = []
            if has_cert:
                cnames = request.form.getlist('course_name[]')
                platforms = request.form.getlist('platform[]')
                certs = request.files.getlist('certificate[]')
                existing_certs = request.form.getlist('existing_course_certificate[]')
                for idx, cname in enumerate(cnames):
                    if cname and cname.strip():
                        cert_file = certs[idx] if idx < len(certs) else None
                        cert_path = validate_and_save_file(cert_file, f'course_{idx}', student_id) if cert_file else ''
                        if not cert_path and idx < len(existing_certs):
                            cert_path = existing_certs[idx]
                        certs_list.append({
                            'course_name': cname.strip(),
                            'platform': platforms[idx] if idx < len(platforms) else '',
                            'certificate_path': cert_path or ''
                        })
            db.save_courses_certificates_card(student_id, certs_list, has_certificate=has_cert)

        elif card_name == 'aptitude':
            skills = request.form.getlist('skill_name[]')
            depths = request.form.getlist('proficiency_level[]')
            skills_list = []
            for sk, dp in zip(skills, depths):
                if sk:
                    skills_list.append({'skill_name': sk, 'proficiency_level': dp})
            db.save_aptitude_card(student_id, skills_list)

        elif card_name == 'communication':
            skills = request.form.getlist('skill_name[]')
            depths = request.form.getlist('proficiency_level[]')
            skills_list = []
            for sk, dp in zip(skills, depths):
                if sk:
                    skills_list.append({'skill_name': sk, 'proficiency_level': dp})
            db.save_communication_card(student_id, skills_list)

        elif card_name == 'foreign_languages':
            langs = request.form.getlist('language_name[]')
            depths = request.form.getlist('proficiency_level[]')
            langs_list = []
            for lg, dp in zip(langs, depths):
                if lg:
                    langs_list.append({'language_name': lg, 'proficiency_level': dp})
            db.save_foreign_languages_card(student_id, langs_list)

        elif card_name == 'projects':
            has_proj = request.form.get('has_project') == 'yes'
            projects_list = []
            if has_proj:
                titles = request.form.getlist('project_title[]')
                urls = request.form.getlist('github_url[]')
                descs = request.form.getlist('project_description[]')
                # array of languages per project passed as json string list
                lang_jsons = request.form.getlist('languages_json[]')
                for idx, t in enumerate(titles):
                    if t and t.strip():
                        projects_list.append({
                            'project_title': t.strip(),
                            'github_url': urls[idx] if idx < len(urls) else '',
                            'project_description': descs[idx] if idx < len(descs) else '',
                            'languages_json': lang_jsons[idx] if idx < len(lang_jsons) else '[]'
                        })
            db.save_projects_card(student_id, projects_list, has_project=has_proj)

        elif card_name == 'pitch':
            answer = request.form.get('answer', '').strip()
            if not answer:
                return jsonify({'success': False, 'message': 'Pitch answer is mandatory and cannot be blank.'}), 400
            words = len(answer.split())
            if words > 1000:
                return jsonify({'success': False, 'message': f'Pitch answer exceeds 1000 words limit (Current: {words} words).'}), 400
            db.save_pitch_card(student_id, answer)

        else:
            return jsonify({'success': False, 'message': 'Unknown card section.'}), 400

        updated_card_data = db.get_student_card_data(student_id)
        return jsonify({
            'success': True,
            'message': f'{card_name.replace("_", " ").title()} card updated successfully!',
            'card_data': updated_card_data
        })

    except ValueError as val_err:
        return jsonify({'success': False, 'message': str(val_err)}), 400
    except Exception as err:
        return jsonify({'success': False, 'message': f'Server error saving card data: {str(err)}'}), 500

@app.route('/api/calculate_score', methods=['POST'])
def calculate_score():
    """Triggers Placement Readiness score calculation across all 13 categories."""
    if not session.get('user_id') or session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized request. Please log in.'}), 401

    try:
        student_id = session['user_id']
        student_record = db.get_student_by_id(student_id)
        card_data = db.get_student_card_data(student_id)

        if not card_data['all_cards_completed']:
            unfilled = [k for k, v in card_data['completion'].items() if not v]
            return jsonify({
                'success': False,
                'message': f'Please complete all 13 cards before calculating your placement readiness score! Unfilled cards: {", ".join(unfilled)}'
            }), 400

        # Execute formula calculation engine
        result = score_engine.compute_placement_readiness(student_record, card_data)

        # Record run in database
        assessment_id = db.record_assessment_run(
            student_id=student_id,
            total_score=result['total_score'],
            classification=result['classification'],
            category_scores=result['category_scores'],
            skill_gaps=result['skill_gaps'],
            recommendations=result['recommendations']
        )

        assessment_history = db.get_assessment_history(student_id)

        # Serialize any datetime objects in assessment_history (PostgreSQL TIMESTAMP)
        for entry in (assessment_history or []):
            if 'assessment_date' in entry and hasattr(entry['assessment_date'], 'isoformat'):
                entry['assessment_date'] = entry['assessment_date'].isoformat()

        return jsonify({
            'success': True,
            'assessment_id': assessment_id,
            'total_score': result['total_score'],
            'classification': result['classification'],
            'category_scores': result['category_scores'],
            'ideal_comparison': result['ideal_comparison'],
            'skill_gaps': result['skill_gaps'],
            'recommendations': result['recommendations'],
            'assessment_history': assessment_history
        })

    except Exception as err:
        import traceback
        print(f"calculate_score error: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error calculating placement score: {str(err)}'}), 500

@app.route('/api/assessment_history')
def get_assessment_history_api():
    """Returns assessment history list."""
    if not session.get('user_id'):
        return jsonify([])
    return jsonify(db.get_assessment_history(session['user_id']))

@app.route('/api/admin/student/<int:student_id>')
def api_admin_student(student_id):
    """API endpoint for Admin to view complete student profile, cards data, assessment history, and skill gaps."""
    if not session.get('user_id') or session.get('role') == 'student':
        return jsonify({'success': False, 'message': 'Unauthorized request. Admin privileges required.'}), 403

    full_profile = db.get_full_student_profile_admin(student_id)
    if not full_profile:
        return jsonify({'success': False, 'message': 'Student not found.'}), 404

    return jsonify({
        'success': True,
        'data': full_profile
    })

@app.route('/api/admin/filter_analytics', methods=['POST'])
def api_admin_filter_analytics():
    """
    API endpoint to dynamically filter cohort data by Department, Academic Year, SGPA,
    Readiness Score, and Backlogs using Pandas, returning updated metrics & Seaborn charts.
    """
    import pandas as pd
    if not session.get('user_id') or session.get('role') == 'student':
        return jsonify({'success': False, 'message': 'Unauthorized request. Admin privileges required.'}), 403

    dept_filter = request.form.get('department', '')
    year_filter = request.form.get('year', '')
    sgpa_filter = request.form.get('sgpa', '')
    status_filter = request.form.get('status', '')
    backlog_filter = request.form.get('backlog', '')

    all_students = db.get_all_students_for_admin()
    if not all_students:
        return jsonify({'success': True, 'students': [], 'metrics': {}, 'charts': {}})

    df = pd.DataFrame(all_students)

    if dept_filter and dept_filter != 'all':
        df = df[df['department_name'] == dept_filter]

    if year_filter and year_filter != 'all':
        df = df[df['current_year'] == year_filter]

    if sgpa_filter and sgpa_filter != 'all':
        if sgpa_filter == 'below_7':
            df = df[df['avg_sgpa'] < 7.0]
        elif sgpa_filter == '7_to_8.5':
            df = df[(df['avg_sgpa'] >= 7.0) & (df['avg_sgpa'] <= 8.5)]
        elif sgpa_filter == 'above_8.5':
            df = df[df['avg_sgpa'] > 8.5]

    if status_filter and status_filter != 'all':
        if status_filter == 'ready':
            df = df[df['total_score'] >= 75.0]
        elif status_filter == 'moderately_ready':
            df = df[(df['total_score'] >= 50.0) & (df['total_score'] < 75.0)]
        elif status_filter == 'needs_improvement':
            df = df[df['total_score'] < 50.0]

    if backlog_filter and backlog_filter != 'all':
        if backlog_filter == 'has_backlog':
            df = df[df['backlogs_count'] > 0]
        elif backlog_filter == 'no_backlog':
            df = df[df['backlogs_count'] == 0]

    filtered_list = df.to_dict(orient='records')
    metrics = admin_analytics.compute_admin_metrics(filtered_list)
    charts = admin_analytics.generate_admin_seaborn_charts(filtered_list)

    return jsonify({
        'success': True,
        'students': filtered_list,
        'metrics': metrics,
        'charts': charts
    })

if __name__ == '__main__':
    print("🚀 Launching CATALYST Web Server on http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
