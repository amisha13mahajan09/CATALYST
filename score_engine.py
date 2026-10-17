"""
CATALYST - Placement Readiness Score Engine & Recommendation Analyzer
Calculates 13-category weighted placement readiness score, generates ideal benchmark comparison,
and builds dynamic personalized gap analysis with actionable suggestions.
"""

def compute_placement_readiness(student_info, card_data):
    """
    Computes placement readiness score out of 100 based on exact weights and parameters:
    1. Academics (10%)
    2. Coding languages (18%)
    3. Technical skills (18%)
    4. Coding platforms (5%)
    5. LinkedIn (0.5%)
    6. Research papers (0.5%)
    7. Internships (1%)
    8. Hackathons (2%)
    9. Courses and certificates (4%)
    10. Aptitude (10%)
    11. Communication skills (10%)
    12. Foreign languages (1%)
    13. Projects (20%)
    """
    current_sem = student_info.get('current_semester', 1) if student_info else 1

    # 1. ACADEMICS (10%)
    acad = card_data.get('academics') or {}
    p10 = float(acad.get('percentage_10th') or 0.0)
    p12 = float(acad.get('percentage_12th') or 0.0)
    
    sgpa_sum = 0.0
    sgpa_count = 0
    for s in range(1, current_sem):
        val = acad.get(f'semester_{s}_sgpa')
        if val is not None:
            sgpa_sum += float(val)
            sgpa_count += 1
    avg_sgpa = (sgpa_sum / sgpa_count) if sgpa_count > 0 else 0.0

    p10_pts = min(2.0, (p10 / 100.0) * 2.0)
    p12_pts = min(2.0, (p12 / 100.0) * 2.0)
    if sgpa_count > 0:
        sgpa_pts = min(6.0, (avg_sgpa / 10.0) * 6.0)
    else:
        avg_school = (p10 + p12) / 2.0
        sgpa_pts = min(6.0, (avg_school / 100.0) * 6.0)

    backlogs = card_data.get('backlogs') or []
    prev_backlogs_count = len(backlogs) if acad.get('previous_backlogs') else 0
    backlog_penalty = prev_backlogs_count * 0.5

    acad_score = max(0.0, min(10.0, p10_pts + p12_pts + sgpa_pts - backlog_penalty))

    # 2. CODING LANGUAGES (18%)
    coding_langs = card_data.get('coding_languages') or []
    prof_map = {
        'beginner': 2, 'intermediate': 4, 'proficient': 6, 'advanced': 8, 'expert': 10,
        '1': 2, '2': 4, '3': 6, '4': 8, '5': 10
    }
    valid_langs = [l for l in coding_langs if l.get('language_name') and l.get('language_name').upper() != 'NONE']
    lang_pts = 0
    for l in valid_langs:
        lvl = str(l.get('proficiency_level', '')).lower()
        lang_pts += prof_map.get(lvl, 4)
    # Target: ~24 points (e.g., 2 proficient + 1 advanced)
    coding_lang_score = min(18.0, (lang_pts / 24.0) * 18.0) if valid_langs else 0.0

    # 3. TECHNICAL SKILLS (18%)
    tech_skills = card_data.get('technical_skills') or []
    valid_tech = [s for s in tech_skills if s.get('skill_name') and s.get('skill_name').upper() != 'NONE']
    tech_pts = 0
    for t in valid_tech:
        lvl = str(t.get('proficiency_level', '')).lower()
        # circle 1-5 or string level
        pts = prof_map.get(lvl, 0)
        if pts == 0:
            try:
                circle_num = int(lvl)
                pts = circle_num * 2
            except ValueError:
                pts = 4
        tech_pts += pts
    # Target: 40 points (e.g. 4 proficient [24] + 2 advanced [16] = 40)
    tech_skills_score = min(18.0, (tech_pts / 40.0) * 18.0) if valid_tech else 0.0

    # 4. CODING PLATFORMS (5%)
    platforms = card_data.get('coding_platforms') or []
    valid_platforms = [p for p in platforms if p.get('platform_name') and p.get('platform_name').upper() != 'NONE']
    total_q_solved = sum(int(p.get('questions_solved') or 0) for p in valid_platforms)
    coding_platforms_score = min(5.0, (total_q_solved / 100.0) * 5.0) if valid_platforms else 0.0

    # 5. LINKEDIN (0.5%)
    linkedin = card_data.get('linkedin') or {}
    uses_linkedin = bool(linkedin.get('uses_for_academic_purposes'))
    post_count = int(linkedin.get('number_of_posts') or 0) if uses_linkedin else 0
    linkedin_score = min(0.5, (post_count / 25.0) * 0.5) if uses_linkedin else 0.0

    # 6. RESEARCH PAPERS (0.5%)
    papers = card_data.get('research_papers') or []
    has_paper = any(p.get('has_published') for p in papers) or len([p for p in papers if p.get('paper_title')]) > 0
    valid_papers = [p for p in papers if p.get('paper_title')]
    research_score = min(0.5, (len(valid_papers) / 1.0) * 0.5) if (has_paper and valid_papers) else 0.0

    # 7. INTERNSHIPS (1%)
    internships = card_data.get('internships') or []
    has_internship = any(i.get('has_internship') for i in internships) or len([i for i in internships if i.get('company_name')]) > 0
    valid_internships = [i for i in internships if i.get('company_name')]
    internships_score = min(1.0, (len(valid_internships) / 1.0) * 1.0) if (has_internship and valid_internships) else 0.0

    # 8. HACKATHONS (2%)
    hackathons = card_data.get('hackathons') or []
    has_hackathon = any(h.get('has_hackathon') for h in hackathons) or len([h for h in hackathons if h.get('hackathon_name')]) > 0
    valid_hackathons = [h for h in hackathons if h.get('hackathon_name')]
    hackathons_score = min(2.0, (len(valid_hackathons) / 1.0) * 2.0) if (has_hackathon and valid_hackathons) else 0.0

    # 9. COURSES AND CERTIFICATES (4%)
    certs = card_data.get('courses_certificates') or []
    has_cert = any(c.get('has_certificate') for c in certs) or len([c for c in certs if c.get('course_name')]) > 0
    valid_certs = [c for c in certs if c.get('course_name')]
    certs_score = min(4.0, (len(valid_certs) / 7.0) * 4.0) if (has_cert and valid_certs) else 0.0

    # 10. APTITUDE (10%)
    aptitude = card_data.get('aptitude') or []
    apt_pts = 0
    for a in aptitude:
        lvl = str(a.get('proficiency_level', '')).lower()
        pts = prof_map.get(lvl, 0)
        if pts == 0:
            try:
                pts = int(lvl) * 2
            except ValueError:
                pts = 4
        apt_pts += pts
    aptitude_score = min(10.0, (apt_pts / 20.0) * 10.0) if aptitude else 0.0

    # 11. COMMUNICATION SKILLS (10%)
    comm = card_data.get('communication') or []
    comm_pts = 0
    for c in comm:
        lvl = str(c.get('proficiency_level', '')).lower()
        pts = prof_map.get(lvl, 0)
        if pts == 0:
            try:
                pts = int(lvl) * 2
            except ValueError:
                pts = 4
        comm_pts += pts
    comm_score = min(10.0, (comm_pts / 20.0) * 10.0) if comm else 0.0

    # 12. FOREIGN LANGUAGES (1%)
    foreign = card_data.get('foreign_languages') or []
    valid_foreign = [f for f in foreign if f.get('language_name') and f.get('language_name').upper() != 'NONE']
    foreign_score = min(1.0, (len(valid_foreign) / 1.0) * 1.0) if valid_foreign else 0.0

    # 13. PROJECTS (20%)
    projects = card_data.get('projects') or []
    has_proj = any(p.get('has_project') for p in projects) or len([p for p in projects if p.get('project_title')]) > 0
    valid_projects = [p for p in projects if p.get('project_title')]
    
    unique_langs = set()
    for p in valid_projects:
        raw_langs = p.get('languages_json') or '[]'
        import json
        try:
            l_list = json.loads(raw_langs) if isinstance(raw_langs, str) else raw_langs
            for l in l_list:
                if l and str(l).strip():
                    unique_langs.add(str(l).strip().lower())
        except Exception:
            pass

    proj_count_score = min(10.0, (len(valid_projects) / 2.0) * 10.0) if (has_proj and valid_projects) else 0.0
    proj_lang_score = min(10.0, (len(unique_langs) / 6.0) * 10.0) if (has_proj and valid_projects) else 0.0
    projects_score = proj_count_score + proj_lang_score

    # CATEGORY BREAKDOWN TABLE
    category_scores = [
        {'category_name': 'Academics', 'category_score': round(acad_score, 2), 'maximum_score': 10.0, 'weightage': 10.0},
        {'category_name': 'Coding Languages', 'category_score': round(coding_lang_score, 2), 'maximum_score': 18.0, 'weightage': 18.0},
        {'category_name': 'Technical Skills', 'category_score': round(tech_skills_score, 2), 'maximum_score': 18.0, 'weightage': 18.0},
        {'category_name': 'Coding Platforms', 'category_score': round(coding_platforms_score, 2), 'maximum_score': 5.0, 'weightage': 5.0},
        {'category_name': 'LinkedIn Profile', 'category_score': round(linkedin_score, 2), 'maximum_score': 0.5, 'weightage': 0.5},
        {'category_name': 'Research Papers', 'category_score': round(research_score, 2), 'maximum_score': 0.5, 'weightage': 0.5},
        {'category_name': 'Internships', 'category_score': round(internships_score, 2), 'maximum_score': 1.0, 'weightage': 1.0},
        {'category_name': 'Hackathons', 'category_score': round(hackathons_score, 2), 'maximum_score': 2.0, 'weightage': 2.0},
        {'category_name': 'Courses & Certificates', 'category_score': round(certs_score, 2), 'maximum_score': 4.0, 'weightage': 4.0},
        {'category_name': 'Aptitude Skills', 'category_score': round(aptitude_score, 2), 'maximum_score': 10.0, 'weightage': 10.0},
        {'category_name': 'Communication Skills', 'category_score': round(comm_score, 2), 'maximum_score': 10.0, 'weightage': 10.0},
        {'category_name': 'Foreign Languages', 'category_score': round(foreign_score, 2), 'maximum_score': 1.0, 'weightage': 1.0},
        {'category_name': 'Projects', 'category_score': round(projects_score, 2), 'maximum_score': 20.0, 'weightage': 20.0},
    ]

    total_score = round(sum(item['category_score'] for item in category_scores), 1)
    
    if total_score >= 85.0:
        classification = 'Ready'
    elif total_score >= 75.0:
        classification = 'Ready'
    elif total_score >= 50.0:
        classification = 'Moderately Ready'
    else:
        classification = 'Needs Improvement'

    # IDEAL BENCHMARK COMPARISON TABLE
    ideal_comparison = [
        {
            'category_name': 'Academics',
            'user_data': f"10th: {p10:.1f}%, 12th: {p12:.1f}%, Avg SGPA: {avg_sgpa:.2f}, Backlogs: {prev_backlogs_count}",
            'ideal_data': "10th >= 80%, 12th >= 75%, Every SGPA >= 8.5, No Backlogs",
            'status': 'Met' if (p10 >= 80 and p12 >= 75 and avg_sgpa >= 8.5 and prev_backlogs_count == 0) else 'Gap Identified'
        },
        {
            'category_name': 'Coding Languages',
            'user_data': f"{len(valid_langs)} languages ({', '.join([l.get('language_name') for l in valid_langs]) if valid_langs else 'None'})",
            'ideal_data': "Any 2 languages Proficient and 1 Advanced",
            'status': 'Met' if coding_lang_score >= 15.0 else 'Gap Identified'
        },
        {
            'category_name': 'Technical Skills',
            'user_data': f"{len(valid_tech)} skills selected",
            'ideal_data': "Any 4 skills Proficient and 2 Advanced",
            'status': 'Met' if tech_skills_score >= 15.0 else 'Gap Identified'
        },
        {
            'category_name': 'Coding Platforms',
            'user_data': f"{total_q_solved} total questions solved",
            'ideal_data': "100+ questions solved on at least 1 platform",
            'status': 'Met' if total_q_solved >= 100 else 'Gap Identified'
        },
        {
            'category_name': 'LinkedIn Profile',
            'user_data': f"{post_count} academic posts ({'Active' if uses_linkedin else 'Inactive'})",
            'ideal_data': "At least 25 academic posts",
            'status': 'Met' if post_count >= 25 else 'Gap Identified'
        },
        {
            'category_name': 'Research Papers',
            'user_data': f"{len(valid_papers)} published paper(s)",
            'ideal_data': "At least 1 published research paper",
            'status': 'Met' if len(valid_papers) >= 1 else 'Gap Identified'
        },
        {
            'category_name': 'Internships',
            'user_data': f"{len(valid_internships)} internship(s)",
            'ideal_data': "At least 1 previous internship",
            'status': 'Met' if len(valid_internships) >= 1 else 'Gap Identified'
        },
        {
            'category_name': 'Hackathons',
            'user_data': f"{len(valid_hackathons)} hackathon(s)",
            'ideal_data': "At least 1 previous hackathon",
            'status': 'Met' if len(valid_hackathons) >= 1 else 'Gap Identified'
        },
        {
            'category_name': 'Courses & Certificates',
            'user_data': f"{len(valid_certs)} certificate(s)",
            'ideal_data': "At least 7 certificates",
            'status': 'Met' if len(valid_certs) >= 7 else 'Gap Identified'
        },
        {
            'category_name': 'Aptitude Skills',
            'user_data': f"Score: {aptitude_score:.1f} / 10.0",
            'ideal_data': "At least 3 advanced aptitude skills",
            'status': 'Met' if aptitude_score >= 8.0 else 'Gap Identified'
        },
        {
            'category_name': 'Communication Skills',
            'user_data': f"Score: {comm_score:.1f} / 10.0",
            'ideal_data': "At least 3 advanced communication skills",
            'status': 'Met' if comm_score >= 8.0 else 'Gap Identified'
        },
        {
            'category_name': 'Foreign Languages',
            'user_data': f"{len(valid_foreign)} foreign language(s) ({', '.join([f.get('language_name') for f in valid_foreign]) if valid_foreign else 'None'})",
            'ideal_data': "English minimum C1 & at least 1 foreign language at least beginner level",
            'status': 'Met' if len(valid_foreign) >= 1 else 'Gap Identified'
        },
        {
            'category_name': 'Projects',
            'user_data': f"{len(valid_projects)} projects, {len(unique_langs)} languages involved",
            'ideal_data': "At least 2 projects with 6 languages involved (html, css, js, java, python, sql, dart, swift, cpp, c, c#, react native, R)",
            'status': 'Met' if (len(valid_projects) >= 2 and len(unique_langs) >= 6) else 'Gap Identified'
        }
    ]

    # GAP ANALYSIS & ACTIONABLE SMART RECOMMENDATIONS TABLE
    skill_gaps = []
    recommendations = []

    # 1. Academics Gap
    if avg_sgpa < 8.5 or prev_backlogs_count > 0 or p10 < 80 or p12 < 75:
        prio = 'High' if (avg_sgpa < 7.5 or prev_backlogs_count > 0) else 'Mid'
        sgpa_target = f"Maintain next semester's SGPA above 8.5"
        suggestion = f"Your current SGPA average is {avg_sgpa:.2f}. " + ("Clear remaining backlogs immediately. " if prev_backlogs_count > 0 else "") + f"Focus on core departmental subjects to boost your engineering SGPA to 8.5+."
        skill_gaps.append({
            'category_name': 'Academics',
            'current_value': f"Avg SGPA {avg_sgpa:.2f}, {prev_backlogs_count} backlog(s)",
            'target_value': "SGPA >= 8.5, 0 Backlogs",
            'gap_description': f"Current SGPA is below 8.5 benchmark." if avg_sgpa < 8.5 else "Backlog history detected.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Academics',
            'recommendation': suggestion,
            'priority': prio
        })

    # 2. Coding Languages Gap
    if coding_lang_score < 15.0:
        prio = 'High'
        known = [l.get('language_name') for l in valid_langs]
        suggest_lang = 'Python' if 'Python' not in known else ('Java' if 'Java' not in known else 'C++')
        suggestion = f"Learn and master {suggest_lang} to Proficient or Advanced level. Practicing data structures and object-oriented concepts in {suggest_lang} will significantly improve technical placement rounds."
        skill_gaps.append({
            'category_name': 'Coding Languages',
            'current_value': f"{len(valid_langs)} language(s) known",
            'target_value': "2 Proficient + 1 Advanced Language",
            'gap_description': "Need deeper proficiency in primary programming languages.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Coding Languages',
            'recommendation': suggestion,
            'priority': prio
        })

    # 3. Technical Skills Gap
    if tech_skills_score < 15.0:
        prio = 'High'
        suggestion = "Strengthen core concepts in Web Development, Databases (SQL/NoSQL), and Data Structures. Target achieving level 4 (Advanced) in at least 2 technical domains."
        skill_gaps.append({
            'category_name': 'Technical Skills',
            'current_value': f"{len(valid_tech)} skills selected",
            'target_value': "4 Proficient + 2 Advanced Technical Skills",
            'gap_description': "Expand technical domain breadth and depth.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Technical Skills',
            'recommendation': suggestion,
            'priority': prio
        })

    # 4. Coding Platforms Gap
    if total_q_solved < 100:
        prio = 'High'
        suggestion = f"You have solved {total_q_solved} questions. Solve 2-3 LeetCode or GeeksforGeeks problems daily to cross the 100+ solved threshold."
        skill_gaps.append({
            'category_name': 'Coding Platforms',
            'current_value': f"{total_q_solved} questions solved",
            'target_value': "100+ Problem Solved on LeetCode/HackerRank",
            'gap_description': f"Need {100 - total_q_solved} more coding problems to reach 100 questions benchmark.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Coding Platforms',
            'recommendation': suggestion,
            'priority': prio
        })

    # 5. LinkedIn Gap
    if post_count < 25:
        prio = 'Mid' if post_count > 10 else 'Low'
        suggestion = "Share project updates, hackathon achievements, and technical learnings on LinkedIn. Build professional network visibility with at least 25 academic posts."
        skill_gaps.append({
            'category_name': 'LinkedIn Profile',
            'current_value': f"{post_count} posts",
            'target_value': "25+ Academic/Technical Posts",
            'gap_description': "Increase professional online presence.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'LinkedIn Profile',
            'recommendation': suggestion,
            'priority': prio
        })

    # 6. Research Papers Gap
    if len(valid_papers) < 1:
        prio = 'Low'
        suggestion = "Collaborate with college faculty or peers to publish a research survey paper or IEEE conference paper in AI, ML, or IoT domains."
        skill_gaps.append({
            'category_name': 'Research Papers',
            'current_value': "0 papers published",
            'target_value': "At least 1 Published Research Paper",
            'gap_description': "No published research papers recorded.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Research Papers',
            'recommendation': suggestion,
            'priority': prio
        })

    # 7. Internships Gap
    if len(valid_internships) < 1:
        prio = 'High'
        suggestion = "Apply for summer/virtual internships on platforms like Internshala, LinkedIn, or Wellfound to gain hands-on corporate experience."
        skill_gaps.append({
            'category_name': 'Internships',
            'current_value': "0 internships",
            'target_value': "At least 1 Industry Internship",
            'gap_description': "Lack of practical industrial experience.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Internships',
            'recommendation': suggestion,
            'priority': prio
        })

    # 8. Hackathons Gap
    if len(valid_hackathons) < 1:
        prio = 'Mid'
        suggestion = "Participate in national hackathons (Smart India Hackathon, Unstop, Devfolio). Hackathons build teamwork, rapid prototyping, and resume highlights."
        skill_gaps.append({
            'category_name': 'Hackathons',
            'current_value': "0 hackathons",
            'target_value': "At least 1 Hackathon Participation",
            'gap_description': "No competitive hackathon participation.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Hackathons',
            'recommendation': suggestion,
            'priority': prio
        })

    # 9. Courses and Certificates Gap
    if len(valid_certs) < 7:
        prio = 'Mid'
        needed = 7 - len(valid_certs)
        suggestion = f"Complete {needed} more technical certifications on Coursera, Udemy, or NPTEL (e.g., AWS, Full Stack Web Dev, Python for Data Science)."
        skill_gaps.append({
            'category_name': 'Courses & Certificates',
            'current_value': f"{len(valid_certs)} certificates",
            'target_value': "7+ Verified Certificates",
            'gap_description': f"Complete {needed} additional certified skill courses.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Courses & Certificates',
            'recommendation': suggestion,
            'priority': prio
        })

    # 10. Aptitude Gap
    if aptitude_score < 8.0:
        prio = 'High'
        suggestion = "Practice Quantitative Aptitude (Profit & Loss, Time & Work) and Logical Reasoning daily. Aptitude tests are the first screening round for 90%+ campus placements."
        skill_gaps.append({
            'category_name': 'Aptitude Skills',
            'current_value': f"Score {aptitude_score:.1f}/10",
            'target_value': "3+ Advanced Aptitude Domains",
            'gap_description': "Aptitude depth needs improvement for campus screening tests.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Aptitude Skills',
            'recommendation': suggestion,
            'priority': prio
        })

    # 11. Communication Skills Gap
    if comm_score < 8.0:
        prio = 'High'
        suggestion = "Practice mock technical interviews and Group Discussions (GD). Focus on structured STAR method answers and confident articulation."
        skill_gaps.append({
            'category_name': 'Communication Skills',
            'current_value': f"Score {comm_score:.1f}/10",
            'target_value': "3+ Advanced Communication Domains",
            'gap_description': "Enhance interview speaking and Group Discussion confidence.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Communication Skills',
            'recommendation': suggestion,
            'priority': prio
        })

    # 12. Foreign Languages Gap
    if len(valid_foreign) < 1:
        prio = 'Low'
        suggestion = "Consider learning a foreign language like Japanese (N5), German (A1), or French (A1) to unlock international career opportunities."
        skill_gaps.append({
            'category_name': 'Foreign Languages',
            'current_value': "None specified",
            'target_value': "1 Foreign Language (Japanese N5 / German A1)",
            'gap_description': "No additional foreign language proficiency listed.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Foreign Languages',
            'recommendation': suggestion,
            'priority': prio
        })

    # 13. Projects Gap
    if len(valid_projects) < 2 or len(unique_langs) < 6:
        prio = 'High'
        suggestion = "Develop at least 2 full-stack projects on GitHub integrating multiple languages (HTML, CSS, JS, Python, SQL, React Native/Java)."
        skill_gaps.append({
            'category_name': 'Projects',
            'current_value': f"{len(valid_projects)} projects, {len(unique_langs)} languages",
            'target_value': "2+ Projects with 6 Stack Languages",
            'gap_description': "Build diverse projects demonstrating full-stack versatility.",
            'priority': prio
        })
        recommendations.append({
            'category_name': 'Projects',
            'recommendation': suggestion,
            'priority': prio
        })

    prio_order = {'High': 1, 'high': 1, 'HIGH': 1, 'Mid': 2, 'mid': 2, 'MID': 2, 'Medium': 2, 'medium': 2, 'MEDIUM': 2, 'Low': 3, 'low': 3, 'LOW': 3}
    skill_gaps.sort(key=lambda x: prio_order.get(x.get('priority'), 99))
    recommendations.sort(key=lambda x: prio_order.get(x.get('priority'), 99))

    return {
        'total_score': total_score,
        'classification': classification,
        'category_scores': category_scores,
        'ideal_comparison': ideal_comparison,
        'skill_gaps': skill_gaps,
        'recommendations': recommendations
    }
