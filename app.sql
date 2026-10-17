


DROP TABLE IF EXISTS recommendations CASCADE;

DROP TABLE IF EXISTS skill_gaps CASCADE;

DROP TABLE IF EXISTS assessment_category_scores CASCADE;

DROP TABLE IF EXISTS assessments CASCADE;

DROP TABLE IF EXISTS project_languages CASCADE;

DROP TABLE IF EXISTS projects CASCADE;

DROP TABLE IF EXISTS foreign_languages CASCADE;

DROP TABLE IF EXISTS aptitude_skills CASCADE;

DROP TABLE IF EXISTS communication_skills CASCADE;

DROP TABLE IF EXISTS courses_certificates CASCADE;

DROP TABLE IF EXISTS hackathons CASCADE;

DROP TABLE IF EXISTS internships CASCADE;

DROP TABLE IF EXISTS research_papers CASCADE;

DROP TABLE IF EXISTS linkedin_profiles CASCADE;

DROP TABLE IF EXISTS coding_platforms CASCADE;

DROP TABLE IF EXISTS technical_skills CASCADE;

DROP TABLE IF EXISTS coding_languages CASCADE;

DROP TABLE IF EXISTS backlogs CASCADE;

DROP TABLE IF EXISTS academic_records CASCADE;

DROP TABLE IF EXISTS students CASCADE;

DROP TABLE IF EXISTS admins CASCADE;

DROP TABLE IF EXISTS departments CASCADE;

DROP TABLE IF EXISTS coding_language_master CASCADE;

DROP TABLE IF EXISTS technical_skill_master CASCADE;

DROP TABLE IF EXISTS aptitude_skill_master CASCADE;

DROP TABLE IF EXISTS communication_skill_master CASCADE;

DROP TABLE IF EXISTS foreign_language_master CASCADE;

DROP TABLE IF EXISTS coding_platform_master CASCADE;




CREATE TABLE admins (

    admin_id SERIAL PRIMARY KEY,

    username VARCHAR(50) UNIQUE NOT NULL,

    password VARCHAR(255) NOT NULL,

    full_name VARCHAR(150) NOT NULL,

    email VARCHAR(150) UNIQUE NOT NULL,

    role VARCHAR(50) NOT NULL DEFAULT 'Placement Coordinator',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (

        role IN (

            'Admin',

            'Faculty',

            'Placement Coordinator'

        )

    )

);




CREATE TABLE departments (

    department_id SERIAL PRIMARY KEY,

    department_name VARCHAR(150) UNIQUE NOT NULL

);

INSERT INTO departments (department_name) VALUES

('Computer Engineering'),

('Computer Science and Engineering'),

('Information Technology'),

('Artificial Intelligence and Machine Learning'),

('Artificial Intelligence and Data Science'),

('Data Science'),

('Electronics and Telecommunication Engineering'),

('Electronics Engineering'),

('Electrical Engineering'),

('Mechanical Engineering'),

('Civil Engineering'),

('Chemical Engineering'),

('Instrumentation Engineering'),

('Production Engineering'),

('Automobile Engineering'),

('Robotics and Automation'),

('Mechatronics Engineering'),

('Biotechnology Engineering'),

('Biomedical Engineering'),

('Aerospace Engineering'),

('Other');



CREATE TABLE students (

    student_id SERIAL PRIMARY KEY,

    prn VARCHAR(30) UNIQUE NOT NULL,

    full_name VARCHAR(150) NOT NULL,

    email VARCHAR(150) UNIQUE NOT NULL,

    password VARCHAR(255) NOT NULL,

    college VARCHAR(200) NOT NULL,

    department_id INTEGER NOT NULL,

    current_year VARCHAR(20) NOT NULL,

    current_semester INTEGER NOT NULL,

    graduation_year INTEGER NOT NULL,

    username VARCHAR(100) UNIQUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id)

        REFERENCES departments(department_id),

    CHECK (

        current_year IN (

            'FE',

            'SE',

            'TE',

            'BE'

        )

    ),

    CHECK (

        current_semester BETWEEN 1 AND 8

    ),

    CHECK (

        graduation_year BETWEEN 2026 AND 2040

    )

);



CREATE TABLE academic_records (

    academic_id SERIAL PRIMARY KEY,

    student_id INTEGER UNIQUE NOT NULL,

    percentage_10th DECIMAL(5,2),

    percentage_12th DECIMAL(5,2),

    semester_1_sgpa DECIMAL(4,2),

    semester_2_sgpa DECIMAL(4,2),

    semester_3_sgpa DECIMAL(4,2),

    semester_4_sgpa DECIMAL(4,2),

    semester_5_sgpa DECIMAL(4,2),

    semester_6_sgpa DECIMAL(4,2),

    semester_7_sgpa DECIMAL(4,2),

    semester_8_sgpa DECIMAL(4,2),

    previous_backlogs BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    CHECK (

        percentage_10th IS NULL

        OR percentage_10th BETWEEN 0 AND 100

    ),

    CHECK (

        percentage_12th IS NULL

        OR percentage_12th BETWEEN 0 AND 100

    ),

    CHECK (

        semester_1_sgpa IS NULL OR semester_1_sgpa BETWEEN 0 AND 10

    ),

    CHECK (

        semester_2_sgpa IS NULL OR semester_2_sgpa BETWEEN 0 AND 10

    ),

    CHECK (

        semester_3_sgpa IS NULL OR semester_3_sgpa BETWEEN 0 AND 10

    ),

    CHECK (

        semester_4_sgpa IS NULL OR semester_4_sgpa BETWEEN 0 AND 10

    ),

    CHECK (

        semester_5_sgpa IS NULL OR semester_5_sgpa BETWEEN 0 AND 10

    ),

    CHECK (

        semester_6_sgpa IS NULL OR semester_6_sgpa BETWEEN 0 AND 10

    ),

    CHECK (

        semester_7_sgpa IS NULL OR semester_7_sgpa BETWEEN 0 AND 10

    ),

    CHECK (

        semester_8_sgpa IS NULL OR semester_8_sgpa BETWEEN 0 AND 10

    )

);


CREATE TABLE backlogs (

    backlog_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    academic_level VARCHAR(20) NOT NULL,

    subject_name VARCHAR(150) NOT NULL,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    CHECK (

        academic_level IN (

            '10th',

            '12th',

            'FE',

            'SE',

            'TE',

            'BE'

        )

    )

);



CREATE TABLE coding_language_master (

    language_id SERIAL PRIMARY KEY,

    language_name VARCHAR(50) UNIQUE NOT NULL

);

INSERT INTO coding_language_master (language_name) VALUES

('NONE'),

('C'),

('C++'),

('C#'),

('Java'),

('Python'),

('JavaScript'),

('TypeScript'),

('Dart'),

('Swift'),

('Kotlin'),

('R'),

('Go'),

('Rust'),

('PHP'),

('Ruby'),

('MATLAB');



CREATE TABLE coding_languages (

    student_language_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    language_id INTEGER NOT NULL,

    proficiency_level VARCHAR(20) NOT NULL,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    FOREIGN KEY (language_id)

        REFERENCES coding_language_master(language_id),

    CHECK (

        proficiency_level IN (

            'Beginner',

            'Intermediate',

            'Proficient',

            'Advanced',

            'Expert'

        )

    ),

    UNIQUE(student_id, language_id)

);



CREATE TABLE technical_skill_master (

    technical_skill_id SERIAL PRIMARY KEY,

    skill_name VARCHAR(100) UNIQUE NOT NULL,

    description TEXT

);

INSERT INTO technical_skill_master

(skill_name, description)

VALUES

('NONE', 'No technical skills selected'),

('Artificial Intelligence',

 'Intelligent systems, AI concepts and AI applications'),

('Machine Learning',

 'Supervised learning, unsupervised learning, regression, classification'),

('Deep Learning',

 'CNNs, RNNs, transformers and deep neural architectures'),

('Neural Networks',

 'ANNs, CNNs, RNNs and neural network fundamentals'),

('NLP',

 'Natural language processing, text processing and language models'),

('Computer Vision',

 'Image processing, object detection and image classification'),

('Generative AI',

 'LLMs, prompt engineering, generative models and AI applications'),

('Data Science',

 'Data analysis, machine learning and statistical modelling'),

('Data Analytics',

 'Data cleaning, analysis and business insights'),

('Data Visualization',

 'Charts, dashboards and visual storytelling'),

('Statistics',

 'Probability, descriptive statistics and inferential statistics'),

('Databases',

 'SQL, NoSQL, PostgreSQL, MySQL, MongoDB and database concepts'),

('Web Development',

 'HTML, CSS, JavaScript, React, backend development and APIs'),

('App Development',

 'Android, Flutter, React Native, iOS and mobile application development'),

('Cloud and DevOps',

 'AWS, Azure, GCP, Docker, CI/CD, Kubernetes and deployment');



CREATE TABLE technical_skills (

    student_skill_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    technical_skill_id INTEGER NOT NULL,

    proficiency_level VARCHAR(20) NOT NULL,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    FOREIGN KEY (technical_skill_id)

        REFERENCES technical_skill_master(technical_skill_id),

    CHECK (

        proficiency_level IN (

            'Beginner',

            'Intermediate',

            'Proficient',

            'Advanced',

            'Expert'

        )

    ),

    UNIQUE(student_id, technical_skill_id)

);




CREATE TABLE coding_platform_master (

    platform_id SERIAL PRIMARY KEY,

    platform_name VARCHAR(100) UNIQUE NOT NULL

);

INSERT INTO coding_platform_master (platform_name) VALUES

('NONE'),

('LeetCode'),

('HackerRank'),

('CodeChef'),

('GeeksforGeeks'),

('Codeforces'),

('Other');




CREATE TABLE coding_platforms (

    coding_platform_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    platform_id INTEGER NOT NULL,

    profile_url TEXT,

    questions_solved INTEGER DEFAULT 0,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    FOREIGN KEY (platform_id)

        REFERENCES coding_platform_master(platform_id),

    CHECK (

        questions_solved >= 0

    )

);




CREATE TABLE linkedin_profiles (

    linkedin_id SERIAL PRIMARY KEY,

    student_id INTEGER UNIQUE NOT NULL,

    uses_for_academic_purposes BOOLEAN NOT NULL,

    profile_url TEXT,

    number_of_posts INTEGER DEFAULT 0,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    CHECK (

        number_of_posts >= 0

    )

);



CREATE TABLE research_papers (

    research_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    paper_title VARCHAR(300) NOT NULL,

    publication_name VARCHAR(300),

    publication_date DATE,

    paper_url TEXT,

    document_path TEXT,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE

);



CREATE TABLE internships (

    internship_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    company_name VARCHAR(200) NOT NULL,

    role VARCHAR(150),

    start_date DATE,

    end_date DATE,

    offer_letter_path TEXT,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    CHECK (

        end_date IS NULL OR start_date IS NULL OR end_date >= start_date

    )

);



CREATE TABLE hackathons (

    hackathon_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    hackathon_name VARCHAR(250) NOT NULL,

    organizer VARCHAR(200),

    participation_date DATE,

    position VARCHAR(50),

    certificate_path TEXT,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE

);



CREATE TABLE courses_certificates (

    certificate_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    course_name VARCHAR(250) NOT NULL,

    platform VARCHAR(150),

    completion_date DATE,

    certificate_path TEXT,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE

);



CREATE TABLE aptitude_skill_master (

    aptitude_skill_id SERIAL PRIMARY KEY,

    skill_name VARCHAR(100) UNIQUE NOT NULL,

    description TEXT

);

INSERT INTO aptitude_skill_master

(skill_name, description)

VALUES

('Quantitative Aptitude',

 'Percentages, profit and loss, ratios, averages, time and work, probability, permutations and combinations'),

('Logical & Analytical Reasoning',

 'Logical reasoning, puzzles, coding-decoding, syllogisms, arrangements and analytical problems'),

('Verbal Ability',

 'Vocabulary, grammar, sentence correction, reading comprehension and verbal reasoning'),

('Data Interpretation & Analysis',

 'Tables, graphs, charts, caselets and numerical data analysis');

CREATE TABLE aptitude_skills (

    student_aptitude_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    aptitude_skill_id INTEGER NOT NULL,

    proficiency_level VARCHAR(20) NOT NULL,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    FOREIGN KEY (aptitude_skill_id)

        REFERENCES aptitude_skill_master(aptitude_skill_id),

    CHECK (

        proficiency_level IN (

            'Beginner',

            'Intermediate',

            'Proficient',

            'Advanced',

            'Expert'

        )

    ),

    UNIQUE(student_id, aptitude_skill_id)

);



CREATE TABLE communication_skill_master (

    communication_skill_id SERIAL PRIMARY KEY,

    skill_name VARCHAR(100) UNIQUE NOT NULL,

    description TEXT

);

INSERT INTO communication_skill_master

(skill_name, description)

VALUES

('Group Discussion',

 'Participation, confidence, listening, teamwork and idea presentation'),

('Conversation',

 'Everyday professional communication and interpersonal interaction'),

('Interview Speaking',

 'Answer structure, confidence, clarity and professional speaking'),

('English Grammar and Vocabulary',

 'Grammar, vocabulary, sentence construction and professional English');

CREATE TABLE communication_skills (

    student_communication_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    communication_skill_id INTEGER NOT NULL,

    proficiency_level VARCHAR(20) NOT NULL,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    FOREIGN KEY (communication_skill_id)

        REFERENCES communication_skill_master(communication_skill_id),

    CHECK (

        proficiency_level IN (

            'Beginner',

            'Intermediate',

            'Proficient',

            'Advanced',

            'Expert'

        )

    ),

    UNIQUE(student_id, communication_skill_id)

);


CREATE TABLE foreign_language_master (

    foreign_language_id SERIAL PRIMARY KEY,

    language_name VARCHAR(100) UNIQUE NOT NULL

);

INSERT INTO foreign_language_master (language_name) VALUES

('Japanese'),

('German'),

('French'),

('Spanish'),

('Italian'),

('Russian'),

('Korean'),

('Chinese'),

('Arabic'),

('Portuguese'),

('Dutch'),

('Mandarin'),

('Other');

CREATE TABLE foreign_languages (

    student_foreign_language_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    foreign_language_id INTEGER NOT NULL,

    proficiency_level VARCHAR(30) NOT NULL,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    FOREIGN KEY (foreign_language_id)

        REFERENCES foreign_language_master(foreign_language_id),

    UNIQUE(student_id, foreign_language_id)

);



CREATE TABLE projects (

    project_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    project_title VARCHAR(250) NOT NULL,

    github_url TEXT,

    project_description TEXT,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE

);

CREATE TABLE project_languages (

    project_language_id SERIAL PRIMARY KEY,

    project_id INTEGER NOT NULL,

    language_id INTEGER NOT NULL,

    FOREIGN KEY (project_id)

        REFERENCES projects(project_id)

        ON DELETE CASCADE,

    FOREIGN KEY (language_id)

        REFERENCES coding_language_master(language_id),

    UNIQUE(project_id, language_id)

);



CREATE TABLE student_pitch (

    pitch_id SERIAL PRIMARY KEY,

    student_id INTEGER UNIQUE NOT NULL,

    answer TEXT NOT NULL,

    word_count INTEGER,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    CHECK (

        word_count IS NULL OR word_count <= 1000

    )

);



CREATE TABLE assessments (

    assessment_id SERIAL PRIMARY KEY,

    student_id INTEGER NOT NULL,

    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    total_score DECIMAL(5,2) NOT NULL,

    classification VARCHAR(50) NOT NULL,

    FOREIGN KEY (student_id)

        REFERENCES students(student_id)

        ON DELETE CASCADE,

    CHECK (

        total_score BETWEEN 0 AND 100

    ),

    CHECK (

        classification IN (

            'Needs Improvement',

            'Moderately Ready',

            'Ready'

        )

    )

);



CREATE TABLE assessment_category_scores (

    category_score_id SERIAL PRIMARY KEY,

    assessment_id INTEGER NOT NULL,

    category_name VARCHAR(100) NOT NULL,

    category_score DECIMAL(5,2) NOT NULL,

    maximum_score DECIMAL(5,2) NOT NULL,

    weightage DECIMAL(5,2) NOT NULL,

    FOREIGN KEY (assessment_id)

        REFERENCES assessments(assessment_id)

        ON DELETE CASCADE,

    CHECK (

        category_score >= 0

    ),

    CHECK (

        maximum_score > 0

    ),

    CHECK (

        weightage >= 0

    ),

    UNIQUE(assessment_id, category_name)

);



CREATE TABLE skill_gaps (

    gap_id SERIAL PRIMARY KEY,

    assessment_id INTEGER NOT NULL,

    category_name VARCHAR(100) NOT NULL,

    current_value TEXT NOT NULL,

    target_value TEXT NOT NULL,

    gap_description TEXT NOT NULL,

    priority VARCHAR(20) NOT NULL,

    FOREIGN KEY (assessment_id)

        REFERENCES assessments(assessment_id)

        ON DELETE CASCADE,

    CHECK (

        priority IN (

            'High',

            'Mid',

            'Medium',

            'Low'

        )

    )

);



CREATE TABLE recommendations (

    recommendation_id SERIAL PRIMARY KEY,

    assessment_id INTEGER NOT NULL,

    category_name VARCHAR(100) NOT NULL,

    recommendation TEXT NOT NULL,

    priority VARCHAR(20) NOT NULL,

    FOREIGN KEY (assessment_id)

        REFERENCES assessments(assessment_id)

        ON DELETE CASCADE,

    CHECK (

        priority IN (

            'High',

            'Mid',

            'Medium',

            'Low'

        )

    )

);



CREATE INDEX idx_students_prn

ON students(prn);

CREATE INDEX idx_students_email

ON students(email);

CREATE INDEX idx_students_department

ON students(department_id);

CREATE INDEX idx_students_year

ON students(current_year);

CREATE INDEX idx_assessments_student

ON assessments(student_id);

CREATE INDEX idx_assessments_score

ON assessments(total_score);

CREATE INDEX idx_assessments_date

ON assessments(assessment_date);



INSERT INTO admins
(username, password, full_name, email, role)
VALUES
('TPC101', 'aaaa', 'Rishikesh Yeolekar', 'tpc101@mmcoe.edu.in', 'Placement Coordinator'),
('TPC102', 'bbbb', 'Ashvini Ahirrao', 'tpc102@mmcoe.edu.in', 'Placement Coordinator'),
('TPC103', 'cccc', 'Avani Anawardekar', 'tpc103@mmcoe.edu.in', 'Placement Coordinator'),
('TPC104', 'dddd', 'Deepali Bhaturkar', 'tpc104@mmcoe.edu.in', 'Placement Coordinator');



INSERT INTO students
(
    prn,
    full_name,
    username,
    email,
    password,
    college,
    department_id,
    current_year,
    current_semester,
    graduation_year
)
VALUES
(
    'B24CE1099',
    'Viraj Joglekar',
    'B24CE1099',
    'virajjoglekar2024.comp@mmcoe.edu.in',
    '253Aries',
    'MMCOE',
    1,
    'TE',
    5,
    2028
),
(
    'B24EL1098',
    'Anagha Sarwate',
    'B24EL1098',
    'anaghasarwate2024.elec@mmcoe.edu.in',
    '263Aries',
    'MMCOE',
    9,
    'TE',
    5,
    2028
),
(
    'B23EL1099',
    'Arnav Modak',
    'B23EL1099',
    'arnavmodak2023.elec@mmcoe.edu.in',
    '273Aries',
    'MMCOE',
    9,
    'BE',
    7,
    2027
),
(
    'B24CE1098',
    'Ishan Mahajan',
    'B24CE1098',
    'ishanmahajan2024.comp@mmcoe.edu.in',
    '283Aries',
    'MMCOE',
    1,
    'TE',
    5,
    2028
),
(
    'B23ME1099',
    'Aryan Patil',
    'B23ME1099',
    'aryanpatil2023.mech@mmcoe.edu.in',
    '293Aries',
    'MMCOE',
    10,
    'BE',
    7,
    2027
);



INSERT INTO academic_records
(
    student_id,
    percentage_10th,
    percentage_12th,
    semester_1_sgpa,
    semester_2_sgpa,
    semester_3_sgpa,
    semester_4_sgpa,
    semester_5_sgpa,
    semester_6_sgpa,
    semester_7_sgpa,
    semester_8_sgpa,
    previous_backlogs
)
VALUES
(1, 89.40, 82.60, 8.70, 9.64, 7.54, 9.23, NULL, NULL, NULL, NULL, FALSE),
(2, 94.20, 91.50, 9.70, 8.64, 9.54, 7.23, NULL, NULL, NULL, NULL, FALSE),
(3, 78.50, 72.40, 8.70, 8.64, 7.54, 9.23, 8.33, 9.21, NULL, NULL, TRUE),
(4, 86.30, 80.20, 9.70, 9.64, 9.54, 9.23, NULL, NULL, NULL, NULL, FALSE),
(5, 82.10, 76.80, 8.60, 8.40, 7.90, 9.60, 8.00, 9.29, NULL, NULL, FALSE);



INSERT INTO backlogs
(student_id, academic_level, subject_name)
VALUES
(3, 'SE', 'Engineering Mathematics III');


INSERT INTO coding_languages
(student_id, language_id, proficiency_level)
VALUES
(1, 6, 'Advanced'),
(1, 2, 'Proficient'),
(1, 3, 'Intermediate'),

(2, 6, 'Expert'),
(2, 5, 'Advanced'),
(2, 7, 'Advanced'),
(2, 3, 'Proficient'),

(3, 6, 'Intermediate'),
(3, 3, 'Intermediate'),

(4, 6, 'Proficient'),
(4, 7, 'Intermediate'),
(4, 13, 'Intermediate'),

(5, 6, 'Advanced'),
(5, 3, 'Advanced'),
(5, 13, 'Proficient');




INSERT INTO technical_skills
(student_id, technical_skill_id, proficiency_level)
VALUES
-- Viraj
(1, 3, 'Advanced'),       -- Machine Learning
(1, 4, 'Proficient'),     -- Deep Learning
(1, 9, 'Proficient'),     -- Data Science
(1, 13, 'Advanced'),      -- Databases
(1, 14, 'Intermediate'),  -- Web Development

-- Anagha
(2, 2, 'Advanced'),       -- Artificial Intelligence
(2, 3, 'Expert'),         -- Machine Learning
(2, 4, 'Advanced'),       -- Deep Learning
(2, 7, 'Advanced'),       -- Computer Vision
(2, 8, 'Advanced'),       -- Generative AI
(2, 9, 'Expert'),         -- Data Science
(2, 13, 'Advanced'),      -- Databases
(2, 14, 'Advanced'),      -- Web Development

-- Arnav
(3, 13, 'Intermediate'),  -- Databases
(3, 14, 'Beginner'),      -- Web Development
(3, 9, 'Intermediate'),   -- Data Science

-- Ishan
(4, 14, 'Proficient'),    -- Web Development
(4, 15, 'Beginner'),      -- App Development
(4, 13, 'Intermediate'),  -- Databases

-- Aryan
(5, 3, 'Advanced'),       -- Machine Learning
(5, 9, 'Advanced'),       -- Data Science
(5, 10, 'Proficient'),    -- Data Analytics
(5, 11, 'Proficient'),    -- Data Visualization
(5, 13, 'Advanced');      -- Databases


INSERT INTO coding_platforms
(student_id, platform_id, profile_url, questions_solved)
VALUES
(1, 2, 'https://leetcode.com/virajjoglekar', 156),
(1, 3, 'https://hackerrank.com/virajjoglekar', 82),
(2, 2, 'https://leetcode.com/anaghasarwate', 420),
(2, 5, 'https://geeksforgeeks.org/user/anaghasarwate', 215),
(3, 2, 'https://leetcode.com/arnavmodak', 48),
(5, 4, 'https://codechef.com/users/aryanpatil', 130);



INSERT INTO linkedin_profiles
(student_id, uses_for_academic_purposes, profile_url, number_of_posts)
VALUES
(1, TRUE, 'https://linkedin.com/in/viraj-joglekar', 18),
(2, TRUE, 'https://linkedin.com/in/anagha-sarwate', 47),
(3, FALSE, NULL, 0),
(4, TRUE, 'https://linkedin.com/in/ishan-mahajan', 12),
(5, TRUE, 'https://linkedin.com/in/aryan-patil', 28);



INSERT INTO research_papers
(student_id, paper_title, publication_name, publication_date, paper_url)
VALUES
(1, 'Machine Learning Based Student Placement Prediction',
 'International Journal of Emerging Technology', '2026-04-15',
 'https://example.com/paper/viraj-placement'),

(2, 'Deep Learning for Automated Medical Image Classification',
 'International Conference on AI', '2026-06-20',
 'https://example.com/paper/anagha-medical-ai'),

(5, 'Data Analytics for Student Performance Prediction',
 'International Journal of Data Science', '2026-07-10',
 'https://example.com/paper/aryan-analytics');



INSERT INTO internships
(student_id, company_name, role, start_date, end_date, offer_letter_path)
VALUES
(1, 'TechNova Solutions', 'Data Science Intern',
 '2026-05-01', '2026-07-31', '/uploads/internships/viraj_offer.pdf'),

(2, 'AI Labs India', 'Machine Learning Intern',
 '2026-05-15', '2026-08-15', '/uploads/internships/anagha_offer.pdf'),

(5, 'DataWorks', 'Data Analyst Intern',
 '2026-06-01', '2026-07-31', '/uploads/internships/aryan_offer.pdf');



INSERT INTO hackathons
(student_id, hackathon_name, organizer, participation_date, position, certificate_path)
VALUES
(1, 'Smart India Hackathon', 'Government of India',
 '2026-03-15', 'Finalist', '/uploads/hackathons/viraj_sih.pdf'),

(2, 'AI Innovation Hackathon', 'Tech Community',
 '2026-05-10', 'Winner', '/uploads/hackathons/anagha_ai.pdf'),

(2, 'Women in Tech Hackathon', 'Women Tech Network',
 '2026-07-05', 'Runner Up', '/uploads/hackathons/anagha_wit.pdf'),

(5, 'DataHack', 'Analytics Community',
 '2026-06-20', 'Participant', '/uploads/hackathons/aryan_datahack.pdf');



INSERT INTO courses_certificates
(student_id, course_name, platform, completion_date, certificate_path)
VALUES
(1, 'Python for Data Science', 'Coursera', '2026-02-10',
 '/uploads/certificates/viraj_python.pdf'),
(1, 'SQL Fundamentals', 'Udemy', '2026-03-15',
 '/uploads/certificates/viraj_sql.pdf'),
(1, 'Machine Learning', 'Coursera', '2026-05-20',
 '/uploads/certificates/viraj_ml.pdf'),

(2, 'Advanced Machine Learning', 'Coursera', '2026-01-20',
 '/uploads/certificates/anagha_ml.pdf'),
(2, 'Deep Learning Specialization', 'Coursera', '2026-03-12',
 '/uploads/certificates/anagha_dl.pdf'),
(2, 'Python Advanced', 'Udemy', '2026-04-18',
 '/uploads/certificates/anagha_python.pdf'),
(2, 'SQL Advanced', 'Udemy', '2026-05-10',
 '/uploads/certificates/anagha_sql.pdf'),
(2, 'Cloud Fundamentals', 'AWS', '2026-06-01',
 '/uploads/certificates/anagha_cloud.pdf'),
(2, 'Data Visualization', 'IBM', '2026-07-12',
 '/uploads/certificates/anagha_visualization.pdf'),
(2, 'Generative AI Fundamentals', 'Google', '2026-08-01',
 '/uploads/certificates/anagha_genai.pdf'),

(3, 'SQL Fundamentals', 'Udemy', '2026-02-15',
 '/uploads/certificates/arnav_sql.pdf'),

(4, 'Web Development Fundamentals', 'Coursera', '2026-04-12',
 '/uploads/certificates/ishan_web.pdf'),
(4, 'Flutter Development', 'Udemy', '2026-06-20',
 '/uploads/certificates/ishan_flutter.pdf'),

(5, 'Python for Everybody', 'Coursera', '2026-02-01',
 '/uploads/certificates/aryan_python.pdf'),
(5, 'Data Analytics', 'Google', '2026-04-05',
 '/uploads/certificates/aryan_analytics.pdf'),
(5, 'SQL for Data Analysis', 'Coursera', '2026-06-10',
 '/uploads/certificates/aryan_sql.pdf');



INSERT INTO aptitude_skills
(student_id, aptitude_skill_id, proficiency_level)
VALUES
(1, 1, 'Proficient'), (1, 2, 'Intermediate'),
(1, 3, 'Advanced'),   (1, 4, 'Proficient'),

(2, 1, 'Advanced'),   (2, 2, 'Advanced'),
(2, 3, 'Advanced'),   (2, 4, 'Proficient'),

(3, 1, 'Intermediate'), (3, 2, 'Beginner'),
(3, 3, 'Intermediate'), (3, 4, 'Beginner'),

(4, 1, 'Proficient'), (4, 2, 'Intermediate'),
(4, 3, 'Proficient'), (4, 4, 'Intermediate'),

(5, 1, 'Advanced'),   (5, 2, 'Proficient'),
(5, 3, 'Proficient'), (5, 4, 'Advanced');



INSERT INTO communication_skills
(student_id, communication_skill_id, proficiency_level)
VALUES
(1, 1, 'Proficient'), (1, 2, 'Advanced'),
(1, 3, 'Proficient'), (1, 4, 'Advanced'),

(2, 1, 'Advanced'), (2, 2, 'Advanced'),
(2, 3, 'Advanced'), (2, 4, 'Expert'),

(3, 1, 'Beginner'), (3, 2, 'Intermediate'),
(3, 3, 'Beginner'), (3, 4, 'Intermediate'),

(4, 1, 'Proficient'), (4, 2, 'Proficient'),
(4, 3, 'Intermediate'), (4, 4, 'Proficient'),

(5, 1, 'Advanced'), (5, 2, 'Proficient'),
(5, 3, 'Advanced'), (5, 4, 'Proficient');



INSERT INTO foreign_languages
(student_id, foreign_language_id, proficiency_level)
VALUES
(1, 1, 'N4'),       -- Japanese
(2, 2, 'B2'),       -- German
(2, 3, 'B1'),       -- French
(4, 1, 'N5'),       -- Japanese
(5, 3, 'A2');       -- French



INSERT INTO projects
(student_id, project_title, github_url, project_description)
VALUES
(1, 'Placement Prediction System',
 'https://github.com/viraj/placement-prediction',
 'Machine learning based placement prediction system.'),

(1, 'Student Management App',
 'https://github.com/viraj/student-management',
 'Web application for managing student records.'),

(2, 'Medical Image Analysis Framework',
 'https://github.com/anagha/medical-image-analysis',
 'Deep learning based medical image classification system.'),

(2, 'AI Resume Analyzer',
 'https://github.com/anagha/ai-resume-analyzer',
 'AI powered resume analysis and skill extraction system.'),

(2, 'Placement Dashboard',
 'https://github.com/anagha/placement-dashboard',
 'Interactive dashboard for placement readiness analytics.'),

(3, 'Library Management System',
 'https://github.com/arnav/library-management',
 'Database driven library management application.'),

(4, 'Smart Campus Mobile App',
 'https://github.com/ishan/smart-campus',
 'Mobile application for campus services and student utilities.'),

(5, 'Sales Analytics Dashboard',
 'https://github.com/aryan/sales-dashboard',
 'Data analytics dashboard for sales performance.');



INSERT INTO project_languages
(project_id, language_id)
VALUES
-- Viraj Project 1
(1, 6), (1, 3), (1, 13),

-- Viraj Project 2
(2, 9), (2, 6), (2, 7),

-- Anagha Project 1
(3, 6), (3, 3), (3, 13),

-- Anagha Project 2
(4, 6), (4, 7), (4, 8),

-- Anagha Project 3
(5, 7), (5, 8), (5, 13),

-- Arnav
(6, 5), (6, 13), (6, 7),

-- Ishan
(7, 9), (7, 7), (7, 13),

-- Aryan
(8, 6), (8, 13), (8, 7);


INSERT INTO student_pitch
(student_id, answer, word_count)
VALUES
(
1,
'I should be considered for this role because I combine strong problem solving skills with practical experience in machine learning, data science and software development. I enjoy learning new technologies and applying them to real world problems. Through academic projects, internships and hackathons, I have developed teamwork, communication and analytical abilities. I am eager to contribute to the organization while continuously improving my technical and professional skills.',
88
),
(
2,
'I bring a combination of technical knowledge, practical project experience, communication skills and a strong willingness to learn. My experience with machine learning, deep learning, data science and application development has allowed me to work on real world problems. I have also participated in hackathons and completed internships, which have helped me develop teamwork and problem solving abilities. I am interested in this role because it provides an opportunity to apply my skills, contribute meaningful solutions and grow with the organization.',
97
),
(
3,
'I am a motivated engineering student who enjoys solving problems and learning new technologies. I have worked on software projects and have developed an interest in databases and application development. I am willing to learn and improve my skills while contributing to the team.',
48
),
(
4,
'I am passionate about software development and enjoy creating useful applications. I have developed projects using web technologies and mobile development tools. I am a quick learner, work well with others and am interested in improving my technical abilities through practical experience.',
49
),
(
5,
'I have developed a strong interest in data science and analytics through academic projects and courses. I enjoy working with data, finding patterns and communicating insights. My internship and project experience has helped me understand how technical knowledge can be applied to real business problems. I am eager to contribute to a team, learn from experienced professionals and grow into a strong data professional.',
78
);



INSERT INTO assessments
(student_id, assessment_date, total_score, classification)
VALUES
(1, '2026-10-03 10:00:00', 70.00, 'Moderately Ready'),
(2, '2026-10-03 10:15:00', 88.00, 'Ready'),
(3, '2026-10-03 10:30:00', 51.00, 'Moderately Ready'),
(4, '2026-10-03 10:45:00', 62.00, 'Moderately Ready'),
(5, '2026-10-03 11:00:00', 74.00, 'Moderately Ready');



INSERT INTO assessment_category_scores
(assessment_id, category_name, category_score, maximum_score, weightage)
VALUES
(1, 'Academics', 7.60, 10, 10),
(1, 'Coding Languages', 12.50, 18, 18),
(1, 'Technical Skills', 12.00, 18, 18),
(1, 'Coding Platforms', 3.40, 5, 5),
(1, 'LinkedIn', 0.36, 0.5, 0.5),
(1, 'Research Papers', 0.30, 0.5, 0.5),
(1, 'Internships', 1.00, 1, 1),
(1, 'Hackathons', 1.20, 2, 2),
(1, 'Courses and Certificates', 2.40, 4, 4),
(1, 'Aptitude', 6.80, 10, 10),
(1, 'Communication Skills', 7.20, 10, 10),
(1, 'Foreign Languages', 0.70, 1, 1),
(1, 'Projects', 13.93, 20, 20),
(2, 'Academics', 8.80, 10, 10),
(2, 'Coding Languages', 16.00, 18, 18),
(2, 'Technical Skills', 16.00, 18, 18),
(2, 'Coding Platforms', 4.50, 5, 5),
(2, 'LinkedIn', 0.45, 0.5, 0.5),
(2, 'Research Papers', 0.50, 0.5, 0.5),
(2, 'Internships', 1.00, 1, 1),
(2, 'Hackathons', 2.00, 2, 2),
(2, 'Courses and Certificates', 3.80, 4, 4),
(2, 'Aptitude', 8.80, 10, 10),
(2, 'Communication Skills', 9.00, 10, 10),
(2, 'Foreign Languages', 0.80, 1, 1),
(2, 'Projects', 15.94, 20, 20),
(3, 'Academics', 5.80, 10, 10),
(3, 'Coding Languages', 6.50, 18, 18),
(3, 'Technical Skills', 6.00, 18, 18),
(3, 'Coding Platforms', 1.20, 5, 5),
(3, 'LinkedIn', 0.00, 0.5, 0.5),
(3, 'Research Papers', 0.00, 0.5, 0.5),
(3, 'Internships', 0.00, 1, 1),
(3, 'Hackathons', 0.50, 2, 2),
(3, 'Courses and Certificates', 1.20, 4, 4),
(3, 'Aptitude', 5.00, 10, 10),
(3, 'Communication Skills', 5.00, 10, 10),
(3, 'Foreign Languages', 0.00, 1, 1),
(3, 'Projects', 19.78, 20, 20),
(4, 'Academics', 7.40, 10, 10),
(4, 'Coding Languages', 8.50, 18, 18),
(4, 'Technical Skills', 18.00, 18, 18),
(4, 'Coding Platforms', 2.00, 5, 5),
(4, 'LinkedIn', 0.24, 0.5, 0.5),
(4, 'Research Papers', 0.00, 0.5, 0.5),
(4, 'Internships', 0.00, 1, 1),
(4, 'Hackathons', 0.00, 2, 2),
(4, 'Courses and Certificates', 1.80, 4, 4),
(4, 'Aptitude', 6.20, 10, 10),
(4, 'Communication Skills', 7.00, 10, 10),
(4, 'Foreign Languages', 0.50, 1, 1),
(4, 'Projects', 11.51, 20, 20),
(5, 'Academics', 7.20, 10, 10),
(5, 'Coding Languages', 11.00, 18, 18),
(5, 'Technical Skills', 12.82, 18, 18),
(5, 'Coding Platforms', 2.80, 5, 5),
(5, 'LinkedIn', 0.28, 0.5, 0.5),
(5, 'Research Papers', 0.30, 0.5, 0.5),
(5, 'Internships', 1.00, 1, 1),
(5, 'Hackathons', 0.60, 2, 2),
(5, 'Courses and Certificates', 2.40, 4, 4),
(5, 'Aptitude', 7.20, 10, 10),
(5, 'Communication Skills', 8.00, 10, 10),
(5, 'Foreign Languages', 0.40, 1, 1),
(5, 'Projects', 20.00, 20, 20);



INSERT INTO skill_gaps
(assessment_id, category_name, current_value, target_value, gap_description, priority)
VALUES
(1, 'Academics', 'Average completed SGPA: 8.78',
 'Maintain SGPA >= 8.5',
 'Maintain consistency and improve the lower semester SGPA values.',
 'Mid'),
(1, 'Coding Languages', 'Python Advanced, C Proficient, C++ Intermediate',
 'At least 2 languages at Advanced/Expert',
 'Improve C++ and continue strengthening core programming skills.',
 'Mid'),
(1, 'Technical Skills', '5 technical skills selected',
 'At least 2 Advanced + 2 Proficient',
 'Develop deeper expertise in machine learning and data science.',
 'Mid'),
(1, 'Coding Platforms', '238 problems solved',
 '300+ problems solved',
 'Increase consistent problem-solving practice.',
 'Mid'),
(1, 'Projects', '2 projects',
 '3+ substantial projects',
 'Add another project with broader technology coverage.',
 'High'),

(3, 'Academics', 'Average completed SGPA: 8.32',
 'Maintain SGPA >= 8.5',
 'Improve academic consistency and address the existing backlog.',
 'High'),
(3, 'Coding Languages', 'Python Intermediate, C++ Intermediate',
 'At least 2 languages at Proficient',
 'Strengthen programming fundamentals and language proficiency.',
 'High'),
(3, 'Coding Platforms', '48 problems solved',
 '200+ problems solved',
 'Build a consistent coding-practice routine.',
 'High'),
(3, 'Communication Skills', 'Beginner to Intermediate',
 'At least Proficient',
 'Practice interview speaking and group discussions.',
 'High');


INSERT INTO recommendations
(assessment_id, category_name, recommendation, priority)
VALUES
(1, 'Academics',
 'Maintain an SGPA above 8.5 and improve consistency across semesters.',
 'Mid'),
(1, 'Coding Languages',
 'Improve C++ from Intermediate to Proficient or Advanced while continuing Python practice.',
 'Mid'),
(1, 'Technical Skills',
 'Build an Advanced-level machine learning or data science project.',
 'High'),
(1, 'Coding Platforms',
 'Increase solved problems gradually and maintain weekly practice.',
 'Mid'),
(1, 'Projects',
 'Build one additional end-to-end project using multiple technologies.',
 'High'),

(2, 'Technical Skills',
 'Continue deepening expertise in machine learning, deep learning and data science.',
 'Low'),
(2, 'Coding Platforms',
 'Maintain regular problem-solving practice despite the already high solved count.',
 'Low'),
(2, 'Projects',
 'Document project impact, architecture and measurable results for placement interviews.',
 'Mid'),

(3, 'Academics',
 'Prioritize clearing the existing backlog and improving semester performance.',
 'High'),
(3, 'Coding Languages',
 'Strengthen Python and C++ through structured practice.',
 'High'),
(3, 'Coding Platforms',
 'Start a consistent coding-practice schedule and gradually increase solved problems.',
 'High'),
(3, 'Communication Skills',
 'Practice interview speaking and group discussions through mock interviews.',
 'High'),

(4, 'Coding Languages',
 'Strengthen programming fundamentals and add another core language at Proficient level.',
 'Mid'),
(4, 'Projects',
 'Expand project experience with a complete deployable application.',
 'Mid'),

(5, 'Coding Platforms',
 'Increase coding-platform activity and maintain weekly problem-solving practice.',
 'Mid'),
(5, 'Communication Skills',
 'Continue improving interview speaking and professional communication.',
 'Low');




CREATE OR REPLACE VIEW latest_student_scores AS

SELECT DISTINCT ON (a.student_id)

    a.student_id,

    s.prn,

    s.full_name,

    s.email,

    d.department_name,

    s.current_year,

    s.current_semester,

    s.graduation_year,

    a.total_score,

    a.classification,

    a.assessment_date

FROM assessments a

JOIN students s

    ON a.student_id = s.student_id

JOIN departments d

    ON s.department_id = d.department_id

ORDER BY

    a.student_id,

    a.assessment_date DESC;



CREATE OR REPLACE VIEW admin_statistics AS

SELECT

    COUNT(*) AS total_students,

    COUNT(*) FILTER (

        WHERE total_score >= 75

    ) AS ready_students,

    COUNT(*) FILTER (

        WHERE total_score >= 50

        AND total_score < 75

    ) AS moderately_ready_students,

    COUNT(*) FILTER (

        WHERE total_score < 50

    ) AS needs_improvement_students,

    ROUND(AVG(total_score), 2) AS average_readiness_score

FROM latest_student_scores;



CREATE OR REPLACE VIEW student_progress AS

SELECT

    a.assessment_id,

    a.student_id,

    s.full_name,

    a.assessment_date,

    a.total_score,

    a.classification

FROM assessments a

JOIN students s

    ON a.student_id = s.student_id

ORDER BY

    a.student_id,

    a.assessment_date;



CREATE OR REPLACE VIEW department_analytics AS

SELECT

    d.department_name,

    COUNT(DISTINCT s.student_id) AS student_count,

    ROUND(

        AVG(ls.total_score),

        2

    ) AS average_readiness_score

FROM students s

JOIN departments d

    ON s.department_id = d.department_id

LEFT JOIN latest_student_scores ls

    ON s.student_id = ls.student_id

GROUP BY

    d.department_name

ORDER BY

    average_readiness_score DESC NULLS LAST;



CREATE OR REPLACE VIEW technical_skill_distribution AS

SELECT

    tsm.skill_name,

    COUNT(ts.student_skill_id) AS number_of_students

FROM technical_skill_master tsm

LEFT JOIN technical_skills ts

    ON tsm.technical_skill_id = ts.technical_skill_id

GROUP BY

    tsm.skill_name

ORDER BY

    number_of_students DESC;



CREATE OR REPLACE VIEW project_participation AS

SELECT

    COUNT(DISTINCT student_id) AS students_with_projects,

    COUNT(*) AS total_projects

FROM projects;



SELECT 'Admins' AS table_name, COUNT(*) AS records
FROM admins

UNION ALL

SELECT 'Students', COUNT(*)
FROM students

UNION ALL

SELECT 'Academic Records', COUNT(*)
FROM academic_records

UNION ALL

SELECT 'Coding Languages', COUNT(*)
FROM coding_languages

UNION ALL

SELECT 'Technical Skills', COUNT(*)
FROM technical_skills

UNION ALL

SELECT 'Coding Platforms', COUNT(*)
FROM coding_platforms

UNION ALL

SELECT 'LinkedIn Profiles', COUNT(*)
FROM linkedin_profiles

UNION ALL

SELECT 'Research Papers', COUNT(*)
FROM research_papers

UNION ALL

SELECT 'Internships', COUNT(*)
FROM internships

UNION ALL

SELECT 'Hackathons', COUNT(*)
FROM hackathons

UNION ALL

SELECT 'Courses / Certificates', COUNT(*)
FROM courses_certificates

UNION ALL

SELECT 'Aptitude Skills', COUNT(*)
FROM aptitude_skills

UNION ALL

SELECT 'Communication Skills', COUNT(*)
FROM communication_skills

UNION ALL

SELECT 'Foreign Languages', COUNT(*)
FROM foreign_languages

UNION ALL

SELECT 'Projects', COUNT(*)
FROM projects

UNION ALL

SELECT 'Assessments', COUNT(*)
FROM assessments

UNION ALL

SELECT 'Skill Gaps', COUNT(*)
FROM skill_gaps

UNION ALL

SELECT 'Recommendations', COUNT(*)
FROM recommendations;



SELECT student_id, prn, full_name, username, email,
       department_id, current_year, current_semester, graduation_year
FROM students
ORDER BY student_id;

SELECT a.assessment_id, a.student_id, s.full_name,
       a.total_score, a.classification
FROM assessments a
JOIN students s ON s.student_id = a.student_id
ORDER BY a.student_id, a.assessment_id;

SELECT assessment_id,
       ROUND(SUM(category_score), 2) AS category_total
FROM assessment_category_scores
GROUP BY assessment_id
ORDER BY assessment_id;