"""
CATALYST - Admin & Student Analytics Engine
Uses NumPy, Pandas, Matplotlib, and Seaborn EXCLUSIVELY for all analytical computations,
at-risk student identification, statistical distribution, and chart generation across the platform.
"""

import os
import io
import base64
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib_cache'
import matplotlib.pyplot as plt
import seaborn as sns

def set_catalyst_theme():
    """Configures Matplotlib and Seaborn to match Catalyst dark UI theme."""
    import warnings
    warnings.filterwarnings('ignore')
    sns.set_theme(style="darkgrid")
    plt.rcParams.update({
        'figure.facecolor': '#111827',
        'axes.facecolor': '#111827',
        'axes.edgecolor': '#374151',
        'axes.labelcolor': '#9ca3af',
        'xtick.color': '#9ca3af',
        'ytick.color': '#9ca3af',
        'grid.color': '#1f2937',
        'text.color': '#ffffff'
    })

def figure_to_base64(fig):
    """Converts a Matplotlib/Seaborn figure to Base64 PNG string."""
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=120, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def compute_admin_metrics(students_list):
    """
    Uses Pandas & NumPy to process student dataset and return administrative summary metrics,
    at-risk student identifications, and weak area analysis.
    """
    if not students_list:
        return {
            'total_students': 0,
            'ready_count': 0,
            'moderately_ready_count': 0,
            'needs_improvement_count': 0,
            'ready_pct': 0.0,
            'mod_pct': 0.0,
            'needs_imp_pct': 0.0,
            'avg_score': 0.0,
            'median_score': 0.0,
            'std_score': 0.0,
            'df': pd.DataFrame(),
            'at_risk_students': []
        }

    # Load data into pandas DataFrame
    df = pd.DataFrame(students_list)

    # Clean numeric columns with numpy/pandas
    df['total_score'] = pd.to_numeric(df.get('total_score', 0), errors='coerce').fillna(0.0)
    df['avg_sgpa'] = pd.to_numeric(df.get('avg_sgpa', 0), errors='coerce').fillna(0.0)
    df['backlogs_count'] = pd.to_numeric(df.get('backlogs_count', 0), errors='coerce').fillna(0)

    # NumPy calculations
    scores_array = df['total_score'].to_numpy()
    total_students = int(len(df))
    ready_count = int(np.sum(scores_array >= 75.0))
    mod_count = int(np.sum((scores_array >= 50.0) & (scores_array < 75.0)))
    needs_imp_count = int(np.sum(scores_array < 50.0))

    ready_pct = round((ready_count / total_students * 100.0), 1) if total_students > 0 else 0.0
    mod_pct = round((mod_count / total_students * 100.0), 1) if total_students > 0 else 0.0
    needs_imp_pct = round((needs_imp_count / total_students * 100.0), 1) if total_students > 0 else 0.0

    avg_score = round(float(np.mean(scores_array)), 1) if total_students > 0 else 0.0
    median_score = round(float(np.median(scores_array)), 1) if total_students > 0 else 0.0
    std_score = round(float(np.std(scores_array)), 1) if total_students > 0 else 0.0

    # Identify At-Risk Students using pandas query/filtering
    # At-risk: total_score < 60 OR SGPA < 7.5 OR backlogs > 0 OR classification == 'Needs Improvement'
    at_risk_mask = (df['total_score'] < 60.0) | (df['avg_sgpa'] < 7.5) | (df['backlogs_count'] > 0)
    at_risk_df = df[at_risk_mask].copy()

    at_risk_list = []
    for idx, row in at_risk_df.iterrows():
        score = row['total_score']
        sgpa = row['avg_sgpa']
        backlogs = row['backlogs_count']
        tech_score = float(row.get('tech_score', 0))
        lang_score = float(row.get('lang_score', 0))
        apt_score = float(row.get('apt_score', 0))
        comm_score = float(row.get('comm_score', 0))
        proj_score = float(row.get('proj_score', 0))

        # Dynamically evaluate weak area based on category score ratios
        # Max scores: Tech 18, Lang 18, Apt 10, Comm 10, Proj 20
        tech_ratio = (tech_score + lang_score) / 36.0
        apt_ratio = apt_score / 10.0
        comm_ratio = comm_score / 10.0
        proj_ratio = proj_score / 20.0

        ratios = {
            'Technical': tech_ratio,
            'Aptitude': apt_ratio,
            'Communication': comm_ratio,
            'Projects': proj_ratio
        }

        # Find min category ratio using numpy
        min_cat = min(ratios, key=ratios.get)

        if backlogs > 0:
            weak_area = f'Academics ({backlogs} Backlog{"s" if backlogs>1 else ""})'
        elif sgpa > 0 and sgpa < 7.0:
            weak_area = f'Academics (SGPA {sgpa:.2f})'
        elif ratios[min_cat] < 0.6:
            weak_area = min_cat
        elif score < 50:
            weak_area = 'Overall Readiness'
        else:
            weak_area = min_cat

        at_risk_list.append({
            'student_id': row.get('student_id'),
            'full_name': row.get('full_name'),
            'prn': row.get('prn'),
            'department_name': row.get('department_name'),
            'current_year': row.get('current_year'),
            'total_score': round(score, 1),
            'avg_sgpa': round(sgpa, 2),
            'classification': row.get('classification', 'Needs Improvement'),
            'weak_area': weak_area
        })

    return {
        'total_students': total_students,
        'ready_count': ready_count,
        'moderately_ready_count': mod_count,
        'needs_improvement_count': needs_imp_count,
        'ready_pct': ready_pct,
        'mod_pct': mod_pct,
        'needs_imp_pct': needs_imp_pct,
        'avg_score': avg_score,
        'median_score': median_score,
        'std_score': std_score,
        'df': df,
        'at_risk_students': at_risk_list
    }

def generate_admin_seaborn_charts(students_list):
    """
    Generates admin analytics charts strictly using Matplotlib & Seaborn over Pandas DataFrames.
    Returns dictionary of Base64-encoded PNG image strings.
    """
    set_catalyst_theme()
    charts = {}

    if not students_list:
        return charts

    df = pd.DataFrame(students_list)
    df['total_score'] = pd.to_numeric(df.get('total_score', 0), errors='coerce').fillna(0.0)

    # 1. Readiness Classification Donut Chart (Matplotlib/Seaborn)
    fig1, ax1 = plt.subplots(figsize=(6, 4.2), facecolor='#111827')
    ax1.set_facecolor('#111827')
    counts = [
        int(np.sum(df['total_score'] >= 75)),
        int(np.sum((df['total_score'] >= 50) & (df['total_score'] < 75))),
        int(np.sum(df['total_score'] < 50))
    ]
    labels = ['Ready (>=75)', 'Moderately Ready (50-74)', 'Needs Improvement (<50)']
    colors = ['#34d399', '#fbbf24', '#f87171']
    
    # Filter non-zero for pie
    filtered_counts = [c for c in counts if c > 0]
    filtered_labels = [l for c, l in zip(counts, labels) if c > 0]
    filtered_colors = [col for c, col in zip(counts, colors) if c > 0]

    if sum(filtered_counts) > 0:
        wedges, texts, autotexts = ax1.pie(
            filtered_counts,
            labels=filtered_labels,
            autopct='%1.1f%%',
            startangle=140,
            colors=filtered_colors,
            pctdistance=0.75,
            textprops=dict(color="#ffffff", fontweight="bold")
        )
        # Create donut center
        centre_circle = plt.Circle((0,0), 0.55, fc='#111827')
        ax1.add_artist(centre_circle)
        ax1.set_title('Cohort Readiness Distribution', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
    charts['chart_classification'] = figure_to_base64(fig1)

    # 2. Score Distribution Histogram & KDE (Seaborn Histplot)
    fig2, ax2 = plt.subplots(figsize=(6.5, 4.2), facecolor='#111827')
    ax2.set_facecolor('#111827')
    sns.histplot(df['total_score'], kde=True, color='#385144', bins=10, ax=ax2, line_kws={'linewidth': 2})
    ax2.set_title('Readiness Score Density & Frequency', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
    ax2.set_xlabel('Total Score (out of 100)', color='#9ca3af', fontsize=10)
    ax2.set_ylabel('Student Count', color='#9ca3af', fontsize=10)
    charts['chart_score_distribution'] = figure_to_base64(fig2)

    # 3. Department-wise Average Readiness Score (Seaborn Barplot)
    fig3, ax3 = plt.subplots(figsize=(7, 4.5), facecolor='#111827')
    ax3.set_facecolor('#111827')
    if 'department_name' in df.columns:
        dept_scores = df.groupby('department_name')['total_score'].mean().reset_index()
        dept_scores = dept_scores.sort_values(by='total_score', ascending=False).head(8)
        sns.barplot(
            data=dept_scores,
            y='department_name',
            x='total_score',
            palette='crest',
            ax=ax3,
            hue='department_name',
            legend=False
        )
        ax3.set_title('Department-wise Average Readiness Score', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
        ax3.set_xlabel('Average Score (0-100)', color='#9ca3af', fontsize=10)
        ax3.set_ylabel('', color='#9ca3af')
        ax3.set_xlim(0, 100)
        for p in ax3.patches:
            width = p.get_width()
            if width > 0:
                ax3.annotate(f'{width:.1f}', (width - 6 if width > 15 else width + 2, p.get_y() + p.get_height() / 2.),
                            ha='center', va='center', fontsize=10, color='#ffffff', fontweight='bold')
    charts['chart_department'] = figure_to_base64(fig3)

    # 4. Year-wise Readiness Score Distribution (Seaborn Boxplot)
    fig4, ax4 = plt.subplots(figsize=(6, 4.2), facecolor='#111827')
    ax4.set_facecolor('#111827')
    if 'current_year' in df.columns:
        year_order = ['FE', 'SE', 'TE', 'BE']
        sns.boxplot(
            data=df,
            x='current_year',
            y='total_score',
            order=year_order,
            palette='coolwarm',
            ax=ax4,
            hue='current_year',
            legend=False
        )
        ax4.set_title('Year-wise Readiness Score Distribution', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
        ax4.set_xlabel('Academic Year', color='#9ca3af', fontsize=10)
        ax4.set_ylabel('Readiness Score (0-100)', color='#9ca3af', fontsize=10)
        ax4.set_ylim(0, 105)
    charts['chart_year'] = figure_to_base64(fig4)

    # 5. 13-Category Average Performance (Matplotlib Horizontal Bar)
    fig5, ax5 = plt.subplots(figsize=(7.5, 5), facecolor='#111827')
    ax5.set_facecolor('#111827')
    cats = ['Academics', 'Coding Langs', 'Tech Skills', 'Platforms', 'LinkedIn', 'Research', 'Internships', 'Hackathons', 'Certificates', 'Aptitude', 'Communication', 'Foreign Langs', 'Projects']
    cat_keys = ['acad_score', 'lang_score', 'tech_score', 'plat_score', 'link_score', 'res_score', 'int_score', 'hack_score', 'cert_score', 'apt_score', 'comm_score', 'for_score', 'proj_score']
    max_weights = [10.0, 18.0, 18.0, 5.0, 0.5, 0.5, 1.0, 2.0, 4.0, 10.0, 10.0, 1.0, 20.0]

    avg_perc = []
    for k, w in zip(cat_keys, max_weights):
        if k in df.columns:
            val = float(df[k].mean())
            avg_perc.append((val / w) * 100.0)
        else:
            avg_perc.append(50.0)

    y_pos = np.arange(len(cats))
    ax5.barh(y_pos, avg_perc, color='#8b5cf6', edgecolor='none', height=0.65)
    ax5.set_yticks(y_pos)
    ax5.set_yticklabels(cats, color='#f9fafb', fontsize=9)
    ax5.invert_yaxis()
    ax5.set_title('Overall 13-Category Performance (% of Max Weightage)', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
    ax5.set_xlabel('Average Score Percentage (%)', color='#9ca3af', fontsize=10)
    ax5.set_xlim(0, 100)
    charts['chart_categories'] = figure_to_base64(fig5)

    # 6. Technical Skill & Language Distribution (Seaborn Barplot)
    fig6, ax6 = plt.subplots(figsize=(6.5, 4.2), facecolor='#111827')
    ax6.set_facecolor('#111827')
    if 'tech_score' in df.columns and 'lang_score' in df.columns:
        tech_means = [
            float(df['tech_score'].mean() / 18.0 * 100),
            float(df['lang_score'].mean() / 18.0 * 100),
            float(df.get('plat_score', pd.Series([0])).mean() / 5.0 * 100)
        ]
        tech_labels = ['Tech Skills', 'Coding Langs', 'Coding Platforms']
        sns.barplot(x=tech_labels, y=tech_means, palette='viridis', ax=ax6, hue=tech_labels, legend=False)
        ax6.set_title('Technical & Coding Competency Level', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
        ax6.set_ylabel('Average Performance (%)', color='#9ca3af', fontsize=10)
        ax6.set_ylim(0, 100)
        for p in ax6.patches:
            h = p.get_height()
            if h > 0:
                ax6.annotate(f'{h:.1f}%', (p.get_x() + p.get_width() / 2., h / 2.),
                            ha='center', va='center', fontsize=10, color='#ffffff', fontweight='bold')
    charts['chart_technical'] = figure_to_base64(fig6)

    # 7. Aptitude & Communication Performance (Seaborn Barplot)
    fig7, ax7 = plt.subplots(figsize=(6, 4.2), facecolor='#111827')
    ax7.set_facecolor('#111827')
    if 'apt_score' in df.columns and 'comm_score' in df.columns:
        soft_means = [
            float(df['apt_score'].mean() / 10.0 * 100),
            float(df['comm_score'].mean() / 10.0 * 100)
        ]
        soft_labels = ['Aptitude Reasoning', 'Communication Skills']
        sns.barplot(x=soft_labels, y=soft_means, palette='magma', ax=ax7, hue=soft_labels, legend=False)
        ax7.set_title('Aptitude & Communication Benchmark', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
        ax7.set_ylabel('Average Performance (%)', color='#9ca3af', fontsize=10)
        ax7.set_ylim(0, 100)
        for p in ax7.patches:
            h = p.get_height()
            if h > 0:
                ax7.annotate(f'{h:.1f}%', (p.get_x() + p.get_width() / 2., h / 2.),
                            ha='center', va='center', fontsize=10, color='#ffffff', fontweight='bold')
    charts['chart_aptitude'] = figure_to_base64(fig7)

    # 8. Project Participation & Practical Experience (Seaborn Barplot)
    fig8, ax8 = plt.subplots(figsize=(6, 4.2), facecolor='#111827')
    ax8.set_facecolor('#111827')
    if 'proj_score' in df.columns:
        proj_means = [
            float(df['proj_score'].mean() / 20.0 * 100),
            float(df.get('int_score', pd.Series([0])).mean() / 1.0 * 100),
            float(df.get('hack_score', pd.Series([0])).mean() / 2.0 * 100)
        ]
        proj_labels = ['Projects', 'Internships', 'Hackathons']
        sns.barplot(x=proj_labels, y=proj_means, palette='Spectral', ax=ax8, hue=proj_labels, legend=False)
        ax8.set_title('Practical Experience & Project Participation', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
        ax8.set_ylabel('Average Performance (%)', color='#9ca3af', fontsize=10)
        ax8.set_ylim(0, 100)
        for p in ax8.patches:
            h = p.get_height()
            if h > 0:
                ax8.annotate(f'{h:.1f}%', (p.get_x() + p.get_width() / 2., h / 2.),
                            ha='center', va='center', fontsize=10, color='#ffffff', fontweight='bold')
    charts['chart_projects'] = figure_to_base64(fig8)

    # 9. At-Risk Weak Area Frequency Distribution (Seaborn Countplot)
    metrics = compute_admin_metrics(students_list)
    at_risk_list = metrics.get('at_risk_students', [])
    fig9, ax9 = plt.subplots(figsize=(6.5, 4.2), facecolor='#111827')
    ax9.set_facecolor('#111827')
    if at_risk_list:
        risk_df = pd.DataFrame(at_risk_list)
        sns.countplot(data=risk_df, y='weak_area', palette='rocket', ax=ax9, hue='weak_area', legend=False)
        ax9.set_title('Students Needing Attention: Primary Deficit Areas', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
        ax9.set_xlabel('Number of Students Affected', color='#9ca3af', fontsize=10)
        ax9.set_ylabel('', color='#9ca3af')
        for p in ax9.patches:
            w = int(p.get_width())
            if w > 0:
                ax9.annotate(f'{w}', (w / 2.0, p.get_y() + p.get_height() / 2.),
                            ha='center', va='center', fontsize=10, color='#ffffff', fontweight='bold')
    else:
        ax9.text(0.5, 0.5, 'No Students Currently At-Risk', ha='center', va='center', color='#34d399', fontsize=14, fontweight='bold')
        ax9.set_axis_off()
    charts['chart_at_risk'] = figure_to_base64(fig9)

    return charts

def generate_student_seaborn_charts(category_scores, assessment_history=None):
    """
    Generates Matplotlib & Seaborn charts for individual student analysis dashboard.
    Replaces client-side JS charting libraries.
    """
    set_catalyst_theme()
    charts = {}

    if not category_scores:
        return charts

    # Ensure no 'Why Should We Hire You' / 'pitch' / 'hire' category is included
    category_scores = [
        cs for cs in category_scores
        if 'hire' not in str(cs.get('category_name', '')).lower()
        and 'pitch' not in str(cs.get('category_name', '')).lower()
    ]
    for cs in category_scores:
        if cs.get('category_name') == 'Projects':
            cs['maximum_score'] = 20.0
            cs['weightage'] = 20.0

    df_cat = pd.DataFrame(category_scores)

    # Chart 1: Category Score vs Weightage (Seaborn Barplot)
    fig1, ax1 = plt.subplots(figsize=(8, 4.5), facecolor='#111827')
    ax1.set_facecolor('#111827')
    
    # Shorten names for display
    name_map = {
        'Academics': 'Acad', 'Coding Languages': 'CodeLang', 'Technical Skills': 'TechSkill',
        'Coding Platforms': 'Platforms', 'LinkedIn Profile': 'LinkedIn', 'Research Papers': 'Research',
        'Internships': 'Intern', 'Hackathons': 'Hackathon', 'Courses & Certificates': 'Certs',
        'Aptitude Skills': 'Aptitude', 'Communication Skills': 'Comm', 'Foreign Languages': 'ForeignLang',
        'Projects': 'Projects'
    }
    df_cat['short_name'] = df_cat['category_name'].map(lambda x: name_map.get(x, x[:8]))
    
    # Calculate % obtained per category using pandas
    df_cat['perc'] = (df_cat['category_score'] / df_cat['maximum_score']) * 100.0

    sns.barplot(data=df_cat, x='short_name', y='perc', palette='crest', ax=ax1, hue='short_name', legend=False)
    ax1.set_title('Your Category Points vs Maximum Weightage (%)', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
    ax1.set_xlabel('Evaluation Category', color='#9ca3af', fontsize=10)
    ax1.set_ylabel('Achieved Score (%)', color='#9ca3af', fontsize=10)
    ax1.set_ylim(0, 105)
    plt.xticks(rotation=40, ha='right')

    for p in ax1.patches:
        h = p.get_height()
        if h > 0:
            ax1.annotate(f'{int(h)}%', (p.get_x() + p.get_width() / 2., h / 2.0),
                        ha='center', va='center', fontsize=8, color='#ffffff', fontweight='bold')
    charts['chart_student_categories'] = figure_to_base64(fig1)

    # Chart 2: Score Weightage Contribution Donut (Matplotlib)
    fig2, ax2 = plt.subplots(figsize=(6, 4.2), facecolor='#111827')
    ax2.set_facecolor('#111827')
    valid_scores = df_cat[df_cat['category_score'] > 0]
    if not valid_scores.empty:
        wedges, texts, autotexts = ax2.pie(
            valid_scores['category_score'],
            labels=valid_scores['short_name'],
            autopct='%1.0f%%',
            startangle=140,
            pctdistance=0.8,
            textprops=dict(color="#ffffff", fontsize=8)
        )
        centre_circle = plt.Circle((0,0), 0.55, fc='#111827')
        ax2.add_artist(centre_circle)
        ax2.set_title('Score Weightage Contribution', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
    charts['chart_student_donut'] = figure_to_base64(fig2)

    # Chart 3: Score Progress Trend Line Chart (Seaborn Lineplot)
    if assessment_history and len(assessment_history) > 0:
        fig3, ax3 = plt.subplots(figsize=(6.5, 3.8), facecolor='#111827')
        ax3.set_facecolor('#111827')
        df_hist = pd.DataFrame(assessment_history)
        df_hist['run'] = np.arange(1, len(df_hist) + 1)
        sns.lineplot(data=df_hist, x='run', y='total_score', marker='o', color='#38bdf8', linewidth=2.5, markersize=8, ax=ax3)
        ax3.set_title('Placement Readiness Score Improvement Trend', color='#ffffff', fontsize=12, fontweight='bold', pad=12)
        ax3.set_xlabel('Assessment Evaluation Run', color='#9ca3af', fontsize=10)
        ax3.set_ylabel('Total Readiness Score (0-100)', color='#9ca3af', fontsize=10)
        ax3.set_ylim(0, 105)
        for idx, row in df_hist.iterrows():
            ax3.annotate(f"{row['total_score']:.1f}", (row['run'], row['total_score'] + 3),
                        ha='center', va='bottom', color='#38bdf8', fontweight='bold', fontsize=9)
        charts['chart_student_trend'] = figure_to_base64(fig3)

    return charts
