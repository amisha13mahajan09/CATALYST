/* ============================================================
   CATALYST - PLACEMENT READINESS ANALYSIS SYSTEM
   Client-Side Scripting, Sectioning Tabs, Modals & Chart Visualizations
   ============================================================ */

let categoryBarChartInstance = null;
let weightageDonutChartInstance = null;
let trendLineChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  // Login Tab Switcher (Student vs Admin/Faculty)
  const tabStudent = document.getElementById('tab-student');
  const tabAdmin = document.getElementById('tab-admin');
  const formStudent = document.getElementById('form-student');
  const formAdmin = document.getElementById('form-admin');

  if (tabStudent && tabAdmin && formStudent && formAdmin) {
    tabStudent.addEventListener('click', () => {
      tabStudent.classList.add('active');
      tabAdmin.classList.remove('active');
      formStudent.style.display = 'block';
      formAdmin.style.display = 'none';
    });

    tabAdmin.addEventListener('click', () => {
      tabAdmin.classList.add('active');
      tabStudent.classList.remove('active');
      formAdmin.style.display = 'block';
      formStudent.style.display = 'none';
    });
  }

  // Password confirmation check on registration form
  const regForm = document.getElementById('student-registration-form');
  if (regForm) {
    regForm.addEventListener('submit', (e) => {
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirm_password').value;
      const errBox = document.getElementById('password-match-error');

      if (password !== confirmPassword) {
        e.preventDefault();
        if (errBox) {
          errBox.style.display = 'block';
          errBox.textContent = 'Passwords do not match. Please re-enter.';
        } else {
          alert('Passwords do not match. Please re-enter.');
        }
      }
    });
  }

  // Initializing charts if assessment data already exists
  if (window.CATALYST_DATA && window.CATALYST_DATA.latest_assessment) {
    initVisualizations();
  }

  // Auto-navigate to results section after score calculation reload
  if (sessionStorage.getItem('catalyst_goto_results') === '1') {
    sessionStorage.removeItem('catalyst_goto_results');
    switchSection('result');
  }

  // Navigation Active State Logic
  const navLinks = document.querySelectorAll('.nav-links .nav-link');
  
  // Set initial active link based on hash
  if (window.location.hash) {
    navLinks.forEach(nav => {
      if (nav.getAttribute('href').includes(window.location.hash)) {
        navLinks.forEach(n => n.classList.remove('active'));
        nav.classList.add('active');
      }
    });
  }

  navLinks.forEach(link => {
    link.addEventListener('click', function() {
      navLinks.forEach(nav => nav.classList.remove('active'));
      this.classList.add('active');
    });
  });

  // If Technical Skills NONE checkbox was pre-checked (existing data), apply disabled state to other cards
  const techNoneCheckbox = document.getElementById('tech-none-checkbox');
  if (techNoneCheckbox && techNoneCheckbox.checked) {
    toggleTechNone(techNoneCheckbox);
  }

  // Initialize project language checkboxes state from saved languages_json hidden inputs
  document.querySelectorAll('.project-langs-json-input').forEach(hiddenInput => {
    const card = hiddenInput.closest('.project-item-card');
    if (!card) return;
    let savedLangs = [];
    try { savedLangs = JSON.parse(hiddenInput.value || '[]'); } catch (e) {}
    if (savedLangs.length > 0) {
      card.querySelectorAll('.project-langs-checkboxes input[type="checkbox"]').forEach(cb => {
        if (savedLangs.includes(cb.value)) cb.checked = true;
      });
    }
  });
});

/* ============================================================
   SECTIONING TABS NAVIGATION
   ============================================================ */
function switchSection(sectionName) {
  const sections = ['dashboard', 'result', 'improvement'];
  sections.forEach(sec => {
    const secEl = document.getElementById(`section-${sec}`);
    const btnEl = document.getElementById(`tab-btn-${sec}`);
    if (secEl && btnEl) {
      if (sec === sectionName) {
        secEl.classList.add('active-section');
        btnEl.classList.add('active');
      } else {
        secEl.classList.remove('active-section');
        btnEl.classList.remove('active');
      }
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Re-render charts when switching to result or improvement sections
  if (sectionName === 'result' || sectionName === 'improvement') {
    setTimeout(initVisualizations, 100);
  }
}

/* ============================================================
   MODALS CONTROLLER
   ============================================================ */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Close modal on clicking outside backdrop
window.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('active');
    document.body.style.overflow = '';
  }
});

/* ============================================================
   5 SMALL CIRCLES PROFICIENCY RATING CONTROLLER
   ============================================================ */
function setCircleRating(circleEl, val) {
  const container = circleEl.closest('.circles-rating-container');
  if (!container) return;

  const valInput = container.querySelector('.circle-val-input');
  if (valInput) {
    valInput.value = val;
  }

  const circles = container.querySelectorAll('.rating-circle');
  circles.forEach((c, idx) => {
    if (idx < val) {
      c.classList.add('active');
    } else {
      c.classList.remove('active');
    }
  });
}

/* ============================================================
   CARD FORMS & DROPDOWN TOGGLE HANDLERS
   ============================================================ */

function toggleBacklogsSection(val) {
  const wrapper = document.getElementById('backlogs-wrapper');
  if (wrapper) {
    wrapper.style.display = (val === 'yes') ? 'block' : 'none';
  }
}

/* Helper to remove a dynamic block and renumber remaining blocks */
function removeDynamicRow(btn) {
  const row = btn.closest('.dynamic-item-row');
  if (row) {
    const container = row.parentElement;
    const allRows = container.querySelectorAll('.dynamic-item-row');
    if (allRows.length > 1) {
      row.remove();
      renumberBoxHeaders(container);
    } else {
      // If it's the only remaining block, clear its inputs
      row.querySelectorAll('input:not([type="checkbox"]):not([type="radio"]), select, textarea').forEach(el => {
        el.value = '';
      });
      row.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach(el => {
        el.checked = false;
      });
      const hiddenJson = row.querySelector('.project-langs-json-input');
      if (hiddenJson) hiddenJson.value = '[]';
    }
  }
}

/* Helper to update item numbering in box headers */
function renumberBoxHeaders(container) {
  if (!container) return;
  const rows = container.querySelectorAll('.dynamic-item-row');
  rows.forEach((r, idx) => {
    const numEl = r.querySelector('.box-item-number');
    if (numEl) numEl.textContent = `#${idx + 1}`;
    const labelEl = r.querySelector('.box-item-label');
    if (labelEl) {
      const base = labelEl.getAttribute('data-base') || labelEl.textContent.replace(/#\d+/, '').trim();
      labelEl.setAttribute('data-base', base);
      labelEl.textContent = `${base} #${idx + 1}`;
    }
  });
}

function addBacklogRow() {
  const container = document.getElementById('backlog-items-container');
  if (container) {
    const idx = container.querySelectorAll('.dynamic-item-row').length + 1;
    const div = document.createElement('div');
    div.className = 'dynamic-item-row backlog-item-row';
    div.innerHTML = `
      <div class="dynamic-box-header">
        <div class="dynamic-box-title">
          <span class="box-item-number">#${idx}</span>
          <span class="box-item-label" data-base="Backlog">Backlog #${idx}</span>
        </div>
        <button type="button" class="btn-remove-item" onclick="removeDynamicRow(this)">✕ Remove</button>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Academic Level</label>
          <select name="backlog_level[]" class="form-control">
            <option value="FE">FE</option>
            <option value="SE">SE</option>
            <option value="TE">TE</option>
            <option value="BE">BE</option>
            <option value="10th">10th</option>
            <option value="12th">12th</option>
          </select>
        </div>
        <div class="form-group">
          <label>Subject Name</label>
          <input type="text" name="backlog_subject[]" placeholder="Subject Name" class="form-control">
        </div>
      </div>
    `;
    container.appendChild(div);
  }
}

function handleLangSelectChange(selectEl) {
  const row = selectEl.closest('.dynamic-item-row');
  if (row) {
    const depthGroup = row.querySelector('.depth-select-group');
    if (depthGroup) {
      depthGroup.style.display = (selectEl.value === 'NONE') ? 'none' : 'block';
    }
  }
}

function addCodingLangRow() {
  const container = document.getElementById('coding-langs-container');
  if (container) {
    const idx = container.querySelectorAll('.dynamic-item-row').length + 1;
    const div = document.createElement('div');
    div.className = 'dynamic-item-row lang-row';
    div.innerHTML = `
      <div class="dynamic-box-header">
        <div class="dynamic-box-title">
          <span class="box-item-number">#${idx}</span>
          <span class="box-item-label" data-base="Language">Language #${idx}</span>
        </div>
        <button type="button" class="btn-remove-item" onclick="removeDynamicRow(this)">✕ Remove</button>
      </div>
      <div class="form-group">
        <label>Programming Language</label>
        <select name="language_name[]" class="form-control lang-select" onchange="handleLangSelectChange(this)">
          <option value="NONE">NONE</option>
          <option value="Python">Python</option>
          <option value="C++">C++</option>
          <option value="Java">Java</option>
          <option value="JavaScript">JavaScript</option>
          <option value="C">C</option>
          <option value="C#">C#</option>
          <option value="TypeScript">TypeScript</option>
          <option value="Dart">Dart</option>
          <option value="Swift">Swift</option>
          <option value="Kotlin">Kotlin</option>
          <option value="R">R</option>
          <option value="Go">Go</option>
          <option value="Rust">Rust</option>
          <option value="PHP">PHP</option>
          <option value="Ruby">Ruby</option>
          <option value="MATLAB">MATLAB</option>
        </select>
      </div>
      <div class="depth-select-group" style="display: none; margin-top: 6px;">
        <label style="font-size: 0.85rem; margin-top: 6px;">Proficiency Depth:</label>
        <select name="proficiency_level[]" class="form-control">
          <option value="Beginner">Beginner</option>
          <option value="Intermediate">Intermediate</option>
          <option value="Proficient">Proficient</option>
          <option value="Advanced">Advanced</option>
          <option value="Expert">Expert</option>
        </select>
      </div>
    `;
    container.appendChild(div);
  }
}

function toggleTechNone(noneCheckbox) {
  const wrapper = document.getElementById('tech-skills-cards-wrapper');
  if (wrapper) {
    const checkboxes = wrapper.querySelectorAll('.tech-checkbox');
    checkboxes.forEach(cb => {
      const card = cb.closest('.tech-skill-card-item');
      const container = card ? card.querySelector('.circles-rating-container') : null;
      const input = card ? card.querySelector('.circle-val-input') : null;
      if (noneCheckbox.checked) {
        cb.checked = false;
        cb.disabled = true;
        if (container) container.style.display = 'none';
        if (input) input.disabled = true;
      } else {
        cb.disabled = false;
      }
    });
  }
}

function toggleTechCardRating(checkboxEl) {
  const card = checkboxEl.closest('.tech-skill-card-item');
  const container = card ? card.querySelector('.circles-rating-container') : null;
  const input = card ? card.querySelector('.circle-val-input') : null;
  if (container) {
    container.style.display = checkboxEl.checked ? 'flex' : 'none';
  }
  if (input) {
    input.disabled = !checkboxEl.checked;
  }
}

function handlePlatformChange(selectEl) {
  const row = selectEl.closest('.platform-item-row');
  if (row) {
    const detailsGroup = row.querySelector('.platform-details-group');
    if (detailsGroup) {
      detailsGroup.style.display = (selectEl.value === 'NONE') ? 'none' : 'block';
    }
  }
}

function addPlatformRow() {
  const container = document.getElementById('platforms-container');
  if (container) {
    const idx = container.querySelectorAll('.dynamic-item-row').length + 1;
    const div = document.createElement('div');
    div.className = 'platform-item-row dynamic-item-row';
    div.innerHTML = `
      <div class="dynamic-box-header">
        <div class="dynamic-box-title">
          <span class="box-item-number">#${idx}</span>
          <span class="box-item-label" data-base="Platform">Platform #${idx}</span>
        </div>
        <button type="button" class="btn-remove-item" onclick="removeDynamicRow(this)">✕ Remove</button>
      </div>
      <div class="form-group">
        <label>Platform Name</label>
        <select name="platform_name[]" class="form-control" onchange="handlePlatformChange(this)">
          <option value="NONE">NONE</option>
          <option value="LeetCode">LeetCode</option>
          <option value="HackerRank">HackerRank</option>
          <option value="CodeChef">CodeChef</option>
          <option value="GeeksforGeeks">GeeksforGeeks</option>
          <option value="Codeforces">Codeforces</option>
          <option value="Other">Other</option>
        </select>
      </div>
      <div class="platform-details-group" style="display: none;">
        <div class="form-group">
          <label>Profile URL</label>
          <input type="url" name="profile_url[]" placeholder="https://leetcode.com/username" class="form-control">
        </div>
        <div class="form-group">
          <label>Total Questions Solved</label>
          <input type="number" min="0" name="questions_solved[]" value="0" class="form-control">
        </div>
      </div>
    `;
    container.appendChild(div);
  }
}

/* ============================================================
   SINGLE FILE UPLOAD UI HANDLERS (STRICT 1 UPLOAD OPTION)
   ============================================================ */
function toggleFileReplace(btn) {
  const container = btn.closest('.single-upload-field');
  if (!container) return;
  const banner = container.querySelector('.existing-file-banner');
  const inputWrap = container.querySelector('.file-input-wrapper');
  if (banner) banner.style.display = 'none';
  if (inputWrap) {
    inputWrap.style.display = 'block';
    const fileInput = inputWrap.querySelector('input[type="file"]');
    if (fileInput) fileInput.focus();
  }
}

function cancelFileReplace(btn) {
  const container = btn.closest('.single-upload-field');
  if (!container) return;
  const banner = container.querySelector('.existing-file-banner');
  const inputWrap = container.querySelector('.file-input-wrapper');
  if (inputWrap) {
    inputWrap.style.display = 'none';
    const fileInput = inputWrap.querySelector('input[type="file"]');
    if (fileInput) fileInput.value = '';
    const preview = inputWrap.querySelector('.selected-file-preview');
    if (preview) {
      preview.style.display = 'none';
      preview.innerHTML = '';
    }
  }
  if (banner) banner.style.display = 'flex';
}

function handleSingleFileSelect(input) {
  const container = input.closest('.single-upload-field') || input.parentElement;
  let preview = container.querySelector('.selected-file-preview');
  if (!preview) {
    preview = document.createElement('div');
    preview.className = 'selected-file-preview';
    container.appendChild(preview);
  }
  if (input.files && input.files.length > 0) {
    const file = input.files[0];
    preview.style.display = 'block';
    preview.innerHTML = `
      <div class="selected-file-badge">
        <span>📄 Ready to upload: <strong>${file.name}</strong></span>
        <button type="button" class="btn-clear-selection" onclick="clearSelectedFile(this)" title="Clear selection">✕ Clear</button>
      </div>
    `;
  } else {
    preview.style.display = 'none';
    preview.innerHTML = '';
  }
}

function clearSelectedFile(btn) {
  const container = btn.closest('.single-upload-field') || btn.closest('.file-input-wrapper') || btn.parentElement.parentElement;
  if (!container) return;
  const fileInput = container.querySelector('input[type="file"]');
  if (fileInput) fileInput.value = '';
  const preview = container.querySelector('.selected-file-preview');
  if (preview) {
    preview.style.display = 'none';
    preview.innerHTML = '';
  }
}

function toggleLinkedInDetails(val) {
  const wrapper = document.getElementById('linkedin-details-wrapper');
  if (wrapper) wrapper.style.display = (val === 'yes') ? 'block' : 'none';
}

function toggleResearchDetails(val) {
  const wrapper = document.getElementById('research-details-wrapper');
  if (wrapper) wrapper.style.display = (val === 'yes') ? 'block' : 'none';
}

function addResearchPaperRow() {
  const container = document.getElementById('research-papers-container');
  if (container) {
    const idx = container.querySelectorAll('.dynamic-item-row').length + 1;
    const div = document.createElement('div');
    div.className = 'dynamic-item-row';
    div.innerHTML = `
      <div class="dynamic-box-header">
        <div class="dynamic-box-title">
          <span class="box-item-number">#${idx}</span>
          <span class="box-item-label" data-base="Research Paper">Research Paper #${idx}</span>
        </div>
        <button type="button" class="btn-remove-item" onclick="removeDynamicRow(this)">✕ Remove</button>
      </div>
      <div class="form-group">
        <label>Paper Title</label>
        <input type="text" name="paper_title[]" class="form-control">
      </div>
      <div class="form-group">
        <label>Journal / Publication Name</label>
        <input type="text" name="publication_name[]" class="form-control">
      </div>
      <div class="form-group">
        <label>Paper URL / Link</label>
        <input type="url" name="paper_url[]" class="form-control">
      </div>
      <div class="form-group">
        <label>Document / Paper Upload (Image/PDF)</label>
        <div class="single-upload-field">
          <input type="hidden" name="existing_paper_document[]" value="">
          <div class="file-input-wrapper">
            <input type="file" name="paper_document[]" accept="image/*,.pdf" class="form-control" onchange="handleSingleFileSelect(this)">
            <div class="selected-file-preview" style="display: none;"></div>
          </div>
        </div>
      </div>
    `;
    container.appendChild(div);
  }
}

function toggleInternshipDetails(val) {
  const wrapper = document.getElementById('internship-details-wrapper');
  if (wrapper) wrapper.style.display = (val === 'yes') ? 'block' : 'none';
}

function addInternshipRow() {
  const container = document.getElementById('internships-container');
  if (container) {
    const idx = container.querySelectorAll('.dynamic-item-row').length + 1;
    const div = document.createElement('div');
    div.className = 'dynamic-item-row';
    div.innerHTML = `
      <div class="dynamic-box-header">
        <div class="dynamic-box-title">
          <span class="box-item-number">#${idx}</span>
          <span class="box-item-label" data-base="Internship">Internship #${idx}</span>
        </div>
        <button type="button" class="btn-remove-item" onclick="removeDynamicRow(this)">✕ Remove</button>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Company Name</label>
          <input type="text" name="company_name[]" class="form-control">
        </div>
        <div class="form-group">
          <label>Role</label>
          <input type="text" name="role[]" class="form-control">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Start Date</label>
          <input type="date" name="start_date[]" class="form-control">
        </div>
        <div class="form-group">
          <label>End Date</label>
          <input type="date" name="end_date[]" class="form-control">
        </div>
      </div>
      <div class="form-group">
        <label>Offer Letter Upload (Image/PDF)</label>
        <div class="single-upload-field">
          <input type="hidden" name="existing_offer_letter[]" value="">
          <div class="file-input-wrapper">
            <input type="file" name="offer_letter[]" accept="image/*,.pdf" class="form-control" onchange="handleSingleFileSelect(this)">
            <div class="selected-file-preview" style="display: none;"></div>
          </div>
        </div>
      </div>
    `;
    container.appendChild(div);
  }
}

function toggleHackathonDetails(val) {
  const wrapper = document.getElementById('hackathon-details-wrapper');
  if (wrapper) wrapper.style.display = (val === 'yes') ? 'block' : 'none';
}

function addHackathonRow() {
  const container = document.getElementById('hackathons-container');
  if (container) {
    const idx = container.querySelectorAll('.dynamic-item-row').length + 1;
    const div = document.createElement('div');
    div.className = 'dynamic-item-row';
    div.innerHTML = `
      <div class="dynamic-box-header">
        <div class="dynamic-box-title">
          <span class="box-item-number">#${idx}</span>
          <span class="box-item-label" data-base="Hackathon">Hackathon #${idx}</span>
        </div>
        <button type="button" class="btn-remove-item" onclick="removeDynamicRow(this)">✕ Remove</button>
      </div>
      <div class="form-group">
        <label>Hackathon Name</label>
        <input type="text" name="hackathon_name[]" class="form-control">
      </div>
      <div class="form-group">
        <label>Organizer</label>
        <input type="text" name="organizer[]" class="form-control">
      </div>
      <div class="form-group">
        <label>Position / Result (e.g. Winner, Finalist, Participant)</label>
        <input type="text" name="position[]" class="form-control">
      </div>
      <div class="form-group">
        <label>Certificate Upload (Image/PDF)</label>
        <div class="single-upload-field">
          <input type="hidden" name="existing_hackathon_certificate[]" value="">
          <div class="file-input-wrapper">
            <input type="file" name="certificate[]" accept="image/*,.pdf" class="form-control" onchange="handleSingleFileSelect(this)">
            <div class="selected-file-preview" style="display: none;"></div>
          </div>
        </div>
      </div>
    `;
    container.appendChild(div);
  }
}

function toggleCoursesDetails(val) {
  const wrapper = document.getElementById('courses-details-wrapper');
  if (wrapper) wrapper.style.display = (val === 'yes') ? 'block' : 'none';
}

function addCourseRow() {
  const container = document.getElementById('courses-container');
  if (container) {
    const idx = container.querySelectorAll('.dynamic-item-row').length + 1;
    const div = document.createElement('div');
    div.className = 'dynamic-item-row';
    div.innerHTML = `
      <div class="dynamic-box-header">
        <div class="dynamic-box-title">
          <span class="box-item-number">#${idx}</span>
          <span class="box-item-label" data-base="Course / Certificate">Course / Certificate #${idx}</span>
        </div>
        <button type="button" class="btn-remove-item" onclick="removeDynamicRow(this)">✕ Remove</button>
      </div>
      <div class="form-group">
        <label>Course Name</label>
        <input type="text" name="course_name[]" class="form-control">
      </div>
      <div class="form-group">
        <label>Platform / Institution (e.g. Coursera, Udemy, NPTEL)</label>
        <input type="text" name="platform[]" class="form-control">
      </div>
      <div class="form-group">
        <label>Certificate Upload (Image/PDF)</label>
        <div class="single-upload-field">
          <input type="hidden" name="existing_course_certificate[]" value="">
          <div class="file-input-wrapper">
            <input type="file" name="certificate[]" accept="image/*,.pdf" class="form-control" onchange="handleSingleFileSelect(this)">
            <div class="selected-file-preview" style="display: none;"></div>
          </div>
        </div>
      </div>
    `;
    container.appendChild(div);
  }
}

function handleForeignSelectChange(selectEl) {
  const row = selectEl.closest('.foreign-lang-row');
  if (row) {
    const group = row.querySelector('.fluency-select-group');
    if (group) group.style.display = (selectEl.value === 'NONE') ? 'none' : 'block';
  }
}

function addForeignLangRow() {
  const container = document.getElementById('foreign-langs-container');
  if (container) {
    const idx = container.querySelectorAll('.dynamic-item-row').length + 1;
    const div = document.createElement('div');
    div.className = 'dynamic-item-row foreign-lang-row';
    div.innerHTML = `
      <div class="dynamic-box-header">
        <div class="dynamic-box-title">
          <span class="box-item-number">#${idx}</span>
          <span class="box-item-label" data-base="Foreign Language">Foreign Language #${idx}</span>
        </div>
        <button type="button" class="btn-remove-item" onclick="removeDynamicRow(this)">✕ Remove</button>
      </div>
      <div class="form-group">
        <label>Foreign Language</label>
        <select name="language_name[]" class="form-control foreign-select" onchange="handleForeignSelectChange(this)">
          <option value="English">English</option>
          <option value="NONE">NONE</option>
          <option value="Japanese">Japanese</option>
          <option value="German">German</option>
          <option value="French">French</option>
          <option value="Spanish">Spanish</option>
          <option value="Italian">Italian</option>
          <option value="Russian">Russian</option>
          <option value="Korean">Korean</option>
          <option value="Chinese">Chinese</option>
          <option value="Arabic">Arabic</option>
          <option value="Portuguese">Portuguese</option>
          <option value="Dutch">Dutch</option>
          <option value="Mandarin">Mandarin</option>
          <option value="Other">Other</option>
        </select>
      </div>
      <div class="fluency-select-group" style="display: none; margin-top: 6px;">
        <label style="font-size: 0.85rem;">Fluency Level:</label>
        <select name="proficiency_level[]" class="form-control">
          <option value="N5 (Beginner)">N5 / A1 (Beginner)</option>
          <option value="N4 (Elementary)">N4 / A2 (Elementary)</option>
          <option value="N3 (Intermediate)">N3 / B1 (Intermediate)</option>
          <option value="N2 (Upper Intermediate)">N2 / B2 (Upper Intermediate)</option>
          <option value="N1 (Advanced/Fluent)">N1 / C1-C2 (Advanced/Fluent)</option>
        </select>
      </div>
    `;
    container.appendChild(div);
  }
}

function toggleProjectDetails(val) {
  const wrapper = document.getElementById('project-details-wrapper');
  if (wrapper) wrapper.style.display = (val === 'yes') ? 'block' : 'none';
}

function updateProjectLangsJSON(checkboxEl) {
  const card = checkboxEl.closest('.project-item-card');
  if (card) {
    const hiddenInput = card.querySelector('.project-langs-json-input');
    const checked = Array.from(card.querySelectorAll('.project-langs-checkboxes input[type="checkbox"]:checked')).map(cb => cb.value);
    if (hiddenInput) hiddenInput.value = JSON.stringify(checked);
  }
}

function addProjectRow() {
  const container = document.getElementById('projects-container');
  if (container) {
    const idx = container.querySelectorAll('.dynamic-item-row').length + 1;
    const div = document.createElement('div');
    div.className = 'dynamic-item-row project-item-card';
    div.innerHTML = `
      <div class="dynamic-box-header">
        <div class="dynamic-box-title">
          <span class="box-item-number">#${idx}</span>
          <span class="box-item-label" data-base="Project">Project #${idx}</span>
        </div>
        <button type="button" class="btn-remove-item" onclick="removeDynamicRow(this)">✕ Remove</button>
      </div>
      <div class="form-group">
        <label>Project Title</label>
        <input type="text" name="project_title[]" class="form-control">
      </div>
      <div class="form-group">
        <label>GitHub Repository Link</label>
        <input type="url" name="github_url[]" placeholder="https://github.com/username/repo" class="form-control">
      </div>
      <div class="form-group">
        <label>Project Description</label>
        <textarea name="project_description[]" rows="2" class="form-control"></textarea>
      </div>
      <div class="form-group">
        <label>Languages & Stack Used (Select all that apply):</label>
        <input type="hidden" name="languages_json[]" class="project-langs-json-input" value="[]">
        <div class="project-langs-checkboxes">
          ${['HTML', 'CSS', 'JavaScript', 'Java', 'Python', 'SQL', 'Dart', 'Swift', 'C++', 'C', 'C#', 'React Native', 'R'].map(l => `
            <label class="checkbox-inline-label">
              <input type="checkbox" value="${l}" onchange="updateProjectLangsJSON(this)"> ${l}
            </label>
          `).join('')}
        </div>
      </div>
    `;
    container.appendChild(div);
  }
}

function updateWordCount(textarea) {
  const text = textarea.value.trim();
  const words = text ? text.split(/\s+/).length : 0;
  const numSpan = document.getElementById('pitch-word-count-num');
  if (numSpan) numSpan.textContent = words;
}

/* ============================================================
   SUBMIT CARD FORM HANDLER (AJAX SAVE & UI UPDATE)
   ============================================================ */
/* ============================================================
   SUBMIT CARD FORM HANDLER (AJAX SAVE & UI UPDATE WITH WARNINGS)
   ============================================================ */
async function submitCardForm(e, cardName) {
  e.preventDefault();
  const form = e.target;
  const modalBody = form.querySelector('.modal-body');

  // Clear previous warning alert banner & field highlights
  const oldWarning = form.querySelector('.modal-warning-alert');
  if (oldWarning) oldWarning.remove();

  const allControls = form.querySelectorAll('.form-control');
  allControls.forEach(ctrl => {
    ctrl.style.borderColor = '';
    ctrl.style.boxShadow = '';
  });

  // Collect missing visible required inputs
  let missingInputs = [];

  allControls.forEach(ctrl => {
    // Skip inputs inside hidden wrapper sections
    const hiddenParent = ctrl.closest('[style*="display: none"], [style*="display:none"]');
    if (hiddenParent) return;

    // Check if input is empty
    const val = ctrl.value ? ctrl.value.trim() : '';
    const isRequired = ctrl.hasAttribute('required') || ctrl.name === 'percentage_10th' || ctrl.name === 'percentage_12th' || ctrl.name === 'answer' || ctrl.name === 'profile_url' || ctrl.name === 'paper_title[]' || ctrl.name === 'company_name[]' || ctrl.name === 'hackathon_name[]' || ctrl.name === 'course_name[]' || ctrl.name === 'project_title[]';

    if (isRequired && val === '') {
      missingInputs.push(ctrl);
    }
  });

  if (missingInputs.length > 0) {
    // Render aesthetic warning alert banner at top of modal body
    if (modalBody) {
      const warnBox = document.createElement('div');
      warnBox.className = 'modal-warning-alert alert alert-warning';
      warnBox.style.marginBottom = '18px';
      warnBox.style.borderRadius = '10px';
      warnBox.style.fontWeight = '700';
      warnBox.style.display = 'flex';
      warnBox.style.alignItems = 'center';
      warnBox.style.gap = '10px';
      warnBox.innerHTML = `⚠️ <span>Warning: Please fill in all required fields before saving.</span>`;
      modalBody.insertBefore(warnBox, modalBody.firstChild);
      modalBody.scrollTop = 0;
    }

    // Highlight missing fields & add live clear handler
    missingInputs.forEach((ctrl, idx) => {
      ctrl.style.borderColor = '#f59e0b';
      ctrl.style.boxShadow = '0 0 0 3px rgba(245, 158, 11, 0.25)';
      if (idx === 0) ctrl.focus();

      ctrl.addEventListener('input', () => {
        ctrl.style.borderColor = '';
        ctrl.style.boxShadow = '';
      }, { once: true });
    });

    return; // Block form submission until details are filled
  }

  const formData = new FormData(form);

  try {
    const res = await fetch(`/api/save_card/${cardName}`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (data.success) {
      closeModal(`modal-${cardName}`);
      window.CATALYST_DATA.card_data = data.card_data;
      updateDashboardCardsUI(data.card_data);
      // Reload page to refresh all modal inputs, file banners, and server-rendered state
      window.location.reload();
    } else {
      alert(data.message || 'Error saving card details.');
    }
  } catch (err) {
    alert(`Error submitting card data: ${err.message}`);
  }
}

/* ============================================================
   UPDATE DASHBOARD CARDS & PROGRESS UI
   ============================================================ */
function getCardSummaryHTML(key, cardData) {
  /* Returns rich summary HTML for each card type */
  try {
    switch (key) {
      case 'academics': {
        const a = cardData.academics;
        if (!a) return '<div class="summary-line">Data Recorded</div>';
        let html = `<div class="summary-line"><strong>10th:</strong> ${a.percentage_10th}% | <strong>12th:</strong> ${a.percentage_12th}%</div>`;
        const sgpas = [];
        for (let s = 1; s <= 8; s++) {
          if (a[`semester_${s}_sgpa`]) {
            sgpas.push(`Sem ${s}: ${a[`semester_${s}_sgpa`]}`);
          }
        }
        if (sgpas.length > 0) {
          html += `<div class="summary-line"><strong>SGPAs:</strong> ${sgpas.join(', ')}</div>`;
        }
        const backlogs = cardData.backlogs || [];
        if (a.previous_backlogs && backlogs.length > 0) {
          html += `<div class="summary-line">⚠️ <strong>Backlogs (${backlogs.length}):</strong> ${backlogs.map(b => `${b.subject_name} (${b.academic_level})`).join(', ')}</div>`;
        } else {
          html += `<div class="summary-line">✓ <strong>Backlogs:</strong> None</div>`;
        }
        const docs = [];
        if (a.marksheet_10th_path) docs.push(`<a href="/static/${a.marksheet_10th_path}" class="doc-badge-link">📄 10th Marksheet</a>`);
        if (a.marksheet_12th_path) docs.push(`<a href="/static/${a.marksheet_12th_path}" class="doc-badge-link">📄 12th Marksheet</a>`);
        if (a.sems_marksheets) {
          Object.entries(a.sems_marksheets).forEach(([sem, path]) => {
            if (path) docs.push(`<a href="/static/${path}" class="doc-badge-link">📄 Sem ${sem}</a>`);
          });
        }
        if (docs.length > 0) {
          html += `<div class="summary-docs-group">${docs.join('')}</div>`;
        }
        return html;
      }
      case 'coding_languages': {
        const langs = cardData.coding_languages || [];
        if (langs.length === 0) return '<div class="summary-line">Data Recorded</div>';
        if (langs[0].language_name === 'NONE') return '<div class="summary-line">None selected</div>';
        const pills = langs.map(l => `<span class="summary-pill"><strong>${l.language_name}</strong>: ${l.proficiency_level}</span>`).join('');
        return `<div class="summary-badges-list">${pills}</div>`;
      }
      case 'technical_skills': {
        const skills = cardData.technical_skills || [];
        if (skills.length === 0) return '<div class="summary-line">Data Recorded</div>';
        if (skills[0].skill_name === 'NONE') return '<div class="summary-line">None selected</div>';
        const pills = skills.map(s => `<span class="summary-pill"><strong>${s.skill_name}</strong> (${s.proficiency_level}/5)</span>`).join('');
        return `<div class="summary-badges-list">${pills}</div>`;
      }
      case 'coding_platforms': {
        const platforms = cardData.coding_platforms || [];
        if (platforms.length === 0) return '<div class="summary-line">Data Recorded</div>';
        if (platforms[0].platform_name === 'NONE') return '<div class="summary-line">None selected</div>';
        return platforms.map(cp => {
          let line = `<strong>${cp.platform_name}:</strong> ${cp.questions_solved || 0} solved`;
          if (cp.profile_url) {
            line += ` <a href="${cp.profile_url}" target="_blank" class="doc-badge-link">🔗 Profile</a>`;
          }
          return `<div class="summary-line">${line}</div>`;
        }).join('');
      }
      case 'linkedin': {
        const li = cardData.linkedin;
        if (!li) return '<div class="summary-line">Data Recorded</div>';
        if (li.uses_for_academic_purposes) {
          let line = `<strong>Academic Usage:</strong> Yes | <strong>Posts:</strong> ${li.number_of_posts || 0}`;
          if (li.profile_url) {
            line += ` <a href="${li.profile_url}" target="_blank" class="doc-badge-link">🔗 Profile</a>`;
          }
          return `<div class="summary-line">${line}</div>`;
        }
        return '<div class="summary-line">Not used for academic purposes</div>';
      }
      case 'research_papers': {
        const papers = (cardData.research_papers || []).filter(p => p.paper_title);
        if (papers.length === 0) return '<div class="summary-line">No research papers published</div>';
        return papers.map(rp => {
          let line = `<strong>${rp.paper_title}</strong>`;
          if (rp.publication_name) line += ` (${rp.publication_name})`;
          if (rp.paper_url) line += ` <a href="${rp.paper_url}" target="_blank" class="doc-badge-link">🔗 Paper Link</a>`;
          if (rp.document_path) line += ` <a href="/static/${rp.document_path}" class="doc-badge-link">📄 ${rp.document_path.split('/').pop()}</a>`;
          return `<div class="summary-line">${line}</div>`;
        }).join('');
      }
      case 'internships': {
        const ints = (cardData.internships || []).filter(i => i.company_name);
        if (ints.length === 0) return '<div class="summary-line">No internships completed</div>';
        return ints.map(it => {
          let line = `<strong>${it.company_name}</strong> - ${it.role || 'Intern'}`;
          if (it.start_date || it.end_date) line += ` (${it.start_date || ''} - ${it.end_date || ''})`;
          if (it.offer_letter_path) line += ` <a href="/static/${it.offer_letter_path}" class="doc-badge-link">📄 ${it.offer_letter_path.split('/').pop()}</a>`;
          return `<div class="summary-line">${line}</div>`;
        }).join('');
      }
      case 'hackathons': {
        const hacks = (cardData.hackathons || []).filter(h => h.hackathon_name);
        if (hacks.length === 0) return '<div class="summary-line">No hackathons attended</div>';
        return hacks.map(hk => {
          let line = `<strong>${hk.hackathon_name}</strong>`;
          if (hk.position) line += ` (${hk.position})`;
          if (hk.certificate_path) line += ` <a href="/static/${hk.certificate_path}" class="doc-badge-link">📄 ${hk.certificate_path.split('/').pop()}</a>`;
          return `<div class="summary-line">${line}</div>`;
        }).join('');
      }
      case 'courses_certificates': {
        const certs = (cardData.courses_certificates || []).filter(c => c.course_name);
        if (certs.length === 0) return '<div class="summary-line">No certifications recorded</div>';
        return certs.map(cr => {
          let line = `<strong>${cr.course_name}</strong>`;
          if (cr.platform) line += ` (${cr.platform})`;
          if (cr.certificate_path) line += ` <a href="/static/${cr.certificate_path}" class="doc-badge-link">📄 ${cr.certificate_path.split('/').pop()}</a>`;
          return `<div class="summary-line">${line}</div>`;
        }).join('');
      }
      case 'aptitude': {
        const apts = cardData.aptitude || [];
        if (apts.length === 0) return '<div class="summary-line">4 Aptitude Domains rated</div>';
        const pills = apts.map(a => `<span class="summary-pill"><strong>${a.skill_name}</strong>: ${a.proficiency_level}/5</span>`).join('');
        return `<div class="summary-badges-list">${pills}</div>`;
      }
      case 'communication': {
        const comms = cardData.communication || [];
        if (comms.length === 0) return '<div class="summary-line">4 Communication Domains rated</div>';
        const pills = comms.map(c => `<span class="summary-pill"><strong>${c.skill_name}</strong>: ${c.proficiency_level}/5</span>`).join('');
        return `<div class="summary-badges-list">${pills}</div>`;
      }
      case 'foreign_languages': {
        const fls = cardData.foreign_languages || [];
        if (fls.length === 0 || fls[0].language_name === 'NONE') return '<div class="summary-line">None selected</div>';
        const pills = fls.map(fl => `<span class="summary-pill"><strong>${fl.language_name}</strong>: ${fl.proficiency_level}</span>`).join('');
        return `<div class="summary-badges-list">${pills}</div>`;
      }
      case 'projects': {
        const projs = (cardData.projects || []).filter(p => p.project_title);
        if (projs.length === 0) return '<div class="summary-line">No projects recorded</div>';
        return projs.map(pr => {
          let line = `<strong>${pr.project_title}</strong>`;
          if (pr.languages_json) {
            try {
              const langs = typeof pr.languages_json === 'string' ? JSON.parse(pr.languages_json) : pr.languages_json;
              if (langs && langs.length > 0) line += ` <span style="font-size: 0.75rem; opacity: 0.85;">[${langs.join(', ')}]</span>`;
            } catch (e) {}
          }
          if (pr.github_url) line += ` <a href="${pr.github_url}" target="_blank" class="doc-badge-link">🔗 GitHub</a>`;
          return `<div class="summary-line">${line}</div>`;
        }).join('');
      }
      default:
        return '<div class="summary-line">Data Recorded</div>';
    }
  } catch (e) {
    return '<div class="summary-line">Data Recorded</div>';
  }
}

function updateDashboardCardsUI(cardData) {
  const completion = cardData.completion;
  const count = cardData.cards_completed_count;

  // Update progress bar
  const fill = document.getElementById('progress-bar-fill');
  const statusTxt = document.getElementById('progress-status-text');
  if (fill) fill.style.width = `${(count / 13.0) * 100}%`;
  if (statusTxt) statusTxt.innerHTML = `Completed <strong>${count}</strong> of 13 cards`;

  // Enable/disable calculate score button
  const calcBtn = document.getElementById('btn-calculate-score');
  if (calcBtn) {
    calcBtn.disabled = !cardData.all_cards_completed;
  }

  // Update card UI classes and completion badges
  for (const [key, isComplete] of Object.entries(completion)) {
    const cardEl = document.getElementById(`card-${key}`);
    if (cardEl) {
      const badge = cardEl.querySelector('.card-status-badge');
      const actionArea = cardEl.querySelector('.card-action-area');
      
      if (isComplete) {
        cardEl.classList.add('completed');
        if (badge) {
          badge.textContent = '✓ Completed';
        }
        if (actionArea) {
          actionArea.innerHTML = `
            <button class="btn btn-secondary edit-card-btn" onclick="openModal('modal-${key}')">✏️ Edit</button>
          `;
        }
      } else {
        cardEl.classList.remove('completed');
        if (badge) badge.textContent = 'Pending';
        if (actionArea) {
          actionArea.innerHTML = `
            <button class="plus-circle-btn" onclick="openModal('modal-${key}')" title="Add Details">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </button>
          `;
        }
      }
    }
  }
}

/* ============================================================
   TRIGGER PLACEMENT READINESS SCORE CALCULATION
   ============================================================ */
async function triggerScoreCalculation() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.add('active');

  try {
    const res = await fetch('/api/calculate_score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();

    setTimeout(() => {
      if (overlay) overlay.classList.remove('active');

      if (data.success) {
        window.CATALYST_DATA.latest_assessment = data;
        window.CATALYST_DATA.assessment_history = data.assessment_history;

        // Flag to auto-navigate to results section after reload
        sessionStorage.setItem('catalyst_goto_results', '1');

        // Refresh Page or render result tables directly
        window.location.reload();
      } else {
        alert(data.message || 'Error calculating placement score.');
      }
    }, 1200);

  } catch (err) {
    if (overlay) overlay.classList.remove('active');
    alert(`Error calculating placement score: ${err.message}`);
  }
}

/* ============================================================
   CHART.JS VISUALIZATIONS INITIALIZATION
   ============================================================ */
function initVisualizations() {
  // All analytics charts across CATALYST are pre-rendered via Matplotlib & Seaborn in Python backend.
  console.log("CATALYST Analytics initialized using Python NumPy, Pandas, Matplotlib, and Seaborn.");
}

/* ============================================================
   ADMIN DASHBOARD DIRECTORY FILTERING & SEARCH
   ============================================================ */
function filterAdminStudentTable() {
  const searchInput = document.getElementById('admin-search-input');
  const searchText = searchInput ? searchInput.value.toLowerCase().trim() : '';

  const deptVal = document.getElementById('admin-filter-dept') ? document.getElementById('admin-filter-dept').value : 'all';
  const yearVal = document.getElementById('admin-filter-year') ? document.getElementById('admin-filter-year').value : 'all';
  const sgpaVal = document.getElementById('admin-filter-sgpa') ? document.getElementById('admin-filter-sgpa').value : 'all';
  const statusVal = document.getElementById('admin-filter-status') ? document.getElementById('admin-filter-status').value : 'all';
  const backlogVal = document.getElementById('admin-filter-backlog') ? document.getElementById('admin-filter-backlog').value : 'all';

  const rows = document.querySelectorAll('#admin-students-table-body tr');

  rows.forEach(row => {
    const name = row.getAttribute('data-name') || '';
    const prn = row.getAttribute('data-prn') || '';
    const dept = row.getAttribute('data-dept') || '';
    const year = row.getAttribute('data-year') || '';
    const sgpa = parseFloat(row.getAttribute('data-sgpa') || '0');
    const status = row.getAttribute('data-status') || '';
    const backlog = parseInt(row.getAttribute('data-backlog') || '0');

    let matchSearch = !searchText || name.includes(searchText) || prn.includes(searchText) || dept.toLowerCase().includes(searchText);
    let matchDept = (deptVal === 'all') || (dept === deptVal);
    let matchYear = (yearVal === 'all') || (year === yearVal);
    
    let matchSgpa = true;
    if (sgpaVal === 'below_7') matchSgpa = (sgpa < 7.0);
    else if (sgpaVal === '7_to_8.5') matchSgpa = (sgpa >= 7.0 && sgpa <= 8.5);
    else if (sgpaVal === 'above_8.5') matchSgpa = (sgpa > 8.5);

    let matchStatus = (statusVal === 'all') || (status === statusVal);

    let matchBacklog = true;
    if (backlogVal === 'has_backlog') matchBacklog = (backlog > 0);
    else if (backlogVal === 'no_backlog') matchBacklog = (backlog === 0);

    if (matchSearch && matchDept && matchYear && matchSgpa && matchStatus && matchBacklog) {
      row.style.display = '';
    } else {
      row.style.display = 'none';
    }
  });

  // Also trigger AJAX request to backend for updating Seaborn charts dynamically
  const formData = new FormData();
  formData.append('department', deptVal);
  formData.append('year', yearVal);
  formData.append('sgpa', sgpaVal);
  formData.append('status', statusVal);
  formData.append('backlog', backlogVal);

  fetch('/api/admin/filter_analytics', {
    method: 'POST',
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    if (data.success && data.charts && data.metrics) {
      // Update Metrics Cards
      const m = data.metrics;
      if (document.getElementById('metric-total-students')) document.getElementById('metric-total-students').textContent = m.total_students;
      if (document.getElementById('metric-ready-count')) document.getElementById('metric-ready-count').innerHTML = `${m.ready_count} <span style="font-size: 1rem; font-weight: 600; color: rgba(52, 211, 153, 0.8);">(${m.ready_pct}%)</span>`;
      if (document.getElementById('metric-mod-count')) document.getElementById('metric-mod-count').innerHTML = `${m.moderately_ready_count} <span style="font-size: 1rem; font-weight: 600; color: rgba(251, 191, 36, 0.8);">(${m.mod_pct}%)</span>`;
      if (document.getElementById('metric-needs-imp-count')) document.getElementById('metric-needs-imp-count').innerHTML = `${m.needs_improvement_count} <span style="font-size: 1rem; font-weight: 600; color: rgba(248, 113, 113, 0.8);">(${m.needs_imp_pct}%)</span>`;

      // Update Base64 Seaborn Charts
      const c = data.charts;
      if (c.chart_classification && document.getElementById('admin-chart-classification')) document.getElementById('admin-chart-classification').src = `data:image/png;base64,${c.chart_classification}`;
      if (c.chart_score_distribution && document.getElementById('admin-chart-score-dist')) document.getElementById('admin-chart-score-dist').src = `data:image/png;base64,${c.chart_score_distribution}`;
      if (c.chart_department && document.getElementById('admin-chart-department')) document.getElementById('admin-chart-department').src = `data:image/png;base64,${c.chart_department}`;
      if (c.chart_year && document.getElementById('admin-chart-year')) document.getElementById('admin-chart-year').src = `data:image/png;base64,${c.chart_year}`;
      if (c.chart_categories && document.getElementById('admin-chart-categories')) document.getElementById('admin-chart-categories').src = `data:image/png;base64,${c.chart_categories}`;
      if (c.chart_technical && document.getElementById('admin-chart-technical')) document.getElementById('admin-chart-technical').src = `data:image/png;base64,${c.chart_technical}`;
      if (c.chart_aptitude && document.getElementById('admin-chart-aptitude')) document.getElementById('admin-chart-aptitude').src = `data:image/png;base64,${c.chart_aptitude}`;
      if (c.chart_projects && document.getElementById('admin-chart-projects')) document.getElementById('admin-chart-projects').src = `data:image/png;base64,${c.chart_projects}`;
      if (c.chart_at_risk && document.getElementById('admin-chart-at-risk')) document.getElementById('admin-chart-at-risk').src = `data:image/png;base64,${c.chart_at_risk}`;
    }
  })
  .catch(err => console.error("Error updating admin analytics:", err));
}

/* ============================================================
   ADMIN DOCUMENT CARD RENDERER & LIGHTBOX VIEWER
   Used in "All 13 Card Data" tab to display uploaded files
   ============================================================ */

/**
 * Renders a compact document thumbnail card for admin inspection.
 * For images: shows a thumbnail preview that opens lightbox on click.
 * For PDFs: shows a PDF icon card that opens lightbox on click.
 * @param {string} label - Display label for the document
 * @param {string} relPath - Relative path like "uploads/filename.pdf"
 * @returns {string} HTML string for the doc card
 */
function renderAdminDocCard(label, relPath) {
  if (!relPath) return '';
  const url = `/static/${relPath}`;
  const isPdf = relPath.toLowerCase().endsWith('.pdf');
  const escapedLabel = label.replace(/'/g, "\\'");
  const escapedUrl = url.replace(/'/g, "\\'");

  if (isPdf) {
    return `
      <div onclick="openAdminDocLightbox('${escapedLabel}', '${escapedUrl}', true)"
           style="cursor:pointer; background: rgba(248,113,113,0.07); border: 1px solid rgba(248,113,113,0.2); border-radius: 8px; padding: 10px 12px; display: flex; align-items: center; gap: 10px; transition: background 0.2s; min-width: 150px; max-width: 200px;"
           onmouseover="this.style.background='rgba(248,113,113,0.14)'" onmouseout="this.style.background='rgba(248,113,113,0.07)'">
        <div style="font-size: 2rem; line-height: 1; flex-shrink: 0;">📄</div>
        <div style="overflow: hidden;">
          <p style="margin: 0; font-size: 0.76rem; font-weight: 700; color: #f87171; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${label}</p>
          <p style="margin: 2px 0 0 0; font-size: 0.68rem; color: var(--text-muted);">PDF · Click to view</p>
        </div>
      </div>
    `;
  } else {
    // Image
    return `
      <div onclick="openAdminDocLightbox('${escapedLabel}', '${escapedUrl}', false)"
           style="cursor:pointer; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; overflow: hidden; width: 160px; flex-shrink: 0; transition: transform 0.2s, box-shadow 0.2s;"
           onmouseover="this.style.transform='scale(1.03)';this.style.boxShadow='0 6px 20px rgba(0,0,0,0.4)'" onmouseout="this.style.transform='';this.style.boxShadow=''">
        <div style="height: 100px; overflow: hidden; background: rgba(0,0,0,0.2);">
          <img src="${url}" alt="${label}"
               style="width: 100%; height: 100%; object-fit: cover; display: block;"
               onerror="this.parentElement.innerHTML='<div style=\\'height:100%;display:flex;align-items:center;justify-content:center;color:var(--text-muted);font-size:0.75rem;\\'>Preview unavailable</div>'">
        </div>
        <div style="padding: 6px 8px; background: rgba(255,255,255,0.03);">
          <p style="margin: 0; font-size: 0.72rem; font-weight: 700; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${label}</p>
          <p style="margin: 1px 0 0 0; font-size: 0.64rem; color: var(--text-muted);">Click to enlarge</p>
        </div>
      </div>
    `;
  }
}

/**
 * Opens the admin document lightbox with the given document.
 * @param {string} title - Title shown in lightbox header
 * @param {string} url - Full URL to the document
 * @param {boolean} isPdf - Whether it's a PDF file
 */
function openAdminDocLightbox(title, url, isPdf) {
  const lb = document.getElementById('admin-doc-lightbox');
  const lbTitle = document.getElementById('admin-doc-lightbox-title');
  const lbOpen = document.getElementById('admin-doc-lightbox-open');
  const lbBody = document.getElementById('admin-doc-lightbox-body');

  if (!lb || !lbTitle || !lbOpen || !lbBody) return;

  lbTitle.textContent = title;
  lbOpen.href = url;

  if (isPdf) {
    lbBody.innerHTML = `
      <iframe src="${url}" style="width: 100%; height: 100%; min-height: 520px; border: none; display: block; background: #fff;"></iframe>
    `;
  } else {
    lbBody.innerHTML = `
      <div style="padding: 16px; text-align: center; max-height: 80vh; overflow: auto;">
        <img src="${url}" alt="${title}"
             style="max-width: 100%; max-height: 70vh; border-radius: 6px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); display: block; margin: 0 auto;"
             onerror="this.outerHTML='<p style=\\'color:#f87171;font-size:0.9rem;\\'>⚠️ Failed to load image. <a href=\\'${url}\\' target=\\'_blank\\' style=\\'color:#38bdf8;\\'>Open directly</a></p>'">
      </div>
    `;
  }

  lb.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

/**
 * Closes the admin document lightbox.
 */
function closeAdminDocLightbox() {
  const lb = document.getElementById('admin-doc-lightbox');
  if (lb) {
    lb.style.display = 'none';
    const lbBody = document.getElementById('admin-doc-lightbox-body');
    if (lbBody) lbBody.innerHTML = ''; // Clear iframe/img to stop loading
  }
  // Only restore scroll if the main student modal is not open
  const mainModal = document.getElementById('modal-student-everything');
  if (!mainModal || mainModal.style.display === 'none') {
    document.body.style.overflow = 'auto';
  }
}

/* ============================================================
   ADMIN "VIEW EVERYTHING" STUDENT INSPECTION MODAL
   ============================================================ */
let currentStudentData = null;

function openStudentEverythingModal(studentId) {
  const modal = document.getElementById('modal-student-everything');
  if (!modal) return;

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  const bodyContent = document.getElementById('modal-student-body-content');
  bodyContent.innerHTML = `
    <div style="text-align: center; padding: 40px;">
      <div class="spinner-ring"></div>
      <p style="margin-top: 12px; color: var(--text-secondary);">Loading full student dataset...</p>
    </div>
  `;

  fetch(`/api/admin/student/${studentId}`)
    .then(res => res.json())
    .then(res => {
      if (!res.success) {
        alert(res.message || 'Failed to fetch student profile');
        closeStudentEverythingModal();
        return;
      }

      currentStudentData = res.data;
      const s = currentStudentData.student;

      document.getElementById('modal-student-name').textContent = s.full_name;
      document.getElementById('modal-student-prn-dept').textContent = `PRN: ${s.prn} | ${s.department_name} (${s.current_year}, Semester ${s.current_semester}) | College: ${s.college}`;

      switchAdminModalTab('profile');
    })
    .catch(err => {
      alert("Error loading student profile: " + err);
      closeStudentEverythingModal();
    });
}

function closeStudentEverythingModal() {
  const modal = document.getElementById('modal-student-everything');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
}

function switchAdminModalTab(tabName) {
  if (!currentStudentData) return;

  const tabs = ['profile', 'scores', 'history', 'gaps', 'cards'];
  tabs.forEach(t => {
    const btn = document.getElementById(`modal-tab-${t}`);
    if (btn) {
      if (t === tabName) btn.classList.add('active');
      else btn.classList.remove('active');
    }
  });

  const bodyContent = document.getElementById('modal-student-body-content');
  const data = currentStudentData;
  const s = data.student;
  const cardData = data.card_data || {};
  const latest = data.latest_assessment;
  const history = data.assessment_history || [];

  if (tabName === 'profile') {
    bodyContent.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
        <div style="background: rgba(255,255,255,0.03); padding: 18px; border-radius: 12px; border: 1px solid var(--border-color);">
          <h4 style="color: var(--accent-primary); margin-bottom: 12px; font-weight: 700;">👤 Personal Details</h4>
          <p style="margin: 6px 0;"><strong>Full Name:</strong> ${s.full_name}</p>
          <p style="margin: 6px 0;"><strong>PRN / Student ID:</strong> ${s.prn}</p>
          <p style="margin: 6px 0;"><strong>Email Address:</strong> <a href="mailto:${s.email}" style="color: var(--accent-primary);">${s.email}</a></p>
          <p style="margin: 6px 0;"><strong>College:</strong> ${s.college}</p>
        </div>

        <div style="background: rgba(255,255,255,0.03); padding: 18px; border-radius: 12px; border: 1px solid var(--border-color);">
          <h4 style="color: var(--accent-primary); margin-bottom: 12px; font-weight: 700;">🎓 Academic Profile</h4>
          <p style="margin: 6px 0;"><strong>Department:</strong> ${s.department_name}</p>
          <p style="margin: 6px 0;"><strong>Current Academic Year:</strong> ${s.current_year}</p>
          <p style="margin: 6px 0;"><strong>Current Semester:</strong> Semester ${s.current_semester}</p>
          <p style="margin: 6px 0;"><strong>Target Graduation Year:</strong> ${s.graduation_year}</p>
        </div>

        <div style="background: rgba(255,255,255,0.03); padding: 18px; border-radius: 12px; border: 1px solid var(--border-color);">
          <h4 style="color: var(--accent-primary); margin-bottom: 12px; font-weight: 700;">📊 Placement Readiness Snapshot</h4>
          <p style="margin: 6px 0;"><strong>Total Readiness Score:</strong> <span style="font-size: 1.2rem; font-weight: 800; color: #38bdf8;">${latest ? latest.total_score : 'Not Evaluated'} / 100</span></p>
          <p style="margin: 6px 0;"><strong>Classification:</strong> <span class="status-badge ${latest && latest.total_score >= 75 ? 'status-ready' : (latest && latest.total_score >= 50 ? 'status-mod' : 'status-needs-imp')}">${latest ? latest.classification : 'N/A'}</span></p>
          <p style="margin: 6px 0;"><strong>Evaluation Date:</strong> ${latest ? (latest.assessment_date || 'Recent') : 'N/A'}</p>
        </div>
      </div>
    `;
  } else if (tabName === 'scores') {
    if (!latest || !latest.category_scores) {
      bodyContent.innerHTML = `<p style="text-align: center; color: var(--text-muted); padding: 30px;">No assessment score breakdown recorded yet for this student.</p>`;
      return;
    }

    let filteredScores = (latest.category_scores || []).filter(cs => {
      let name = (cs.category_name || '').toLowerCase();
      return !name.includes('hire') && !name.includes('pitch');
    });

    let rowsHtml = filteredScores.map(cs => {
      let maxScore = cs.category_name === 'Projects' ? 20.0 : cs.maximum_score;
      let perc = (cs.category_score / maxScore) * 100.0;
      return `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
          <td style="padding: 10px 14px; font-weight: 600;">${cs.category_name}</td>
          <td style="padding: 10px 14px; text-align: right; font-weight: 700; color: #38bdf8;">${cs.category_score.toFixed(2)}</td>
          <td style="padding: 10px 14px; text-align: right; color: var(--text-muted);">${maxScore.toFixed(2)}</td>
          <td style="padding: 10px 14px; text-align: right; font-weight: 700; color: ${perc >= 75 ? '#34d399' : (perc >= 50 ? '#fbbf24' : '#f87171')};">${perc.toFixed(1)}%</td>
        </tr>
      `;
    }).join('');

    bodyContent.innerHTML = `
      <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 12px; padding: 16px;">
        <h4 style="margin-bottom: 12px; font-weight: 700;">13 Evaluation Category Breakdown</h4>
        <table class="data-table" style="width: 100%; border-collapse: collapse; font-size: 0.88rem;">
          <thead>
            <tr style="background: rgba(255,255,255,0.04); text-align: left;">
              <th style="padding: 10px 14px;">Category</th>
              <th style="padding: 10px 14px; text-align: right;">Points Scored</th>
              <th style="padding: 10px 14px; text-align: right;">Max Weightage</th>
              <th style="padding: 10px 14px; text-align: right;">Achieved %</th>
            </tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>
    `;
  } else if (tabName === 'history') {
    if (!history || history.length === 0) {
      bodyContent.innerHTML = `<p style="text-align: center; color: var(--text-muted); padding: 30px;">No assessment history records found.</p>`;
      return;
    }

    let hRows = history.map((h, idx) => `
      <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
        <td style="padding: 10px 14px; font-weight: 600;">Run #${idx + 1}</td>
        <td style="padding: 10px 14px; color: var(--text-muted);">${h.assessment_date || 'Date N/A'}</td>
        <td style="padding: 10px 14px; font-weight: 800; color: #38bdf8;">${h.total_score} / 100</td>
        <td style="padding: 10px 14px;">
          <span class="status-badge ${h.total_score >= 75 ? 'status-ready' : (h.total_score >= 50 ? 'status-mod' : 'status-needs-imp')}">
            ${h.classification}
          </span>
        </td>
      </tr>
    `).join('');

    bodyContent.innerHTML = `
      <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 12px; padding: 16px;">
        <h4 style="margin-bottom: 12px; font-weight: 700;">Past Score Run Trajectory</h4>
        <table class="data-table" style="width: 100%; border-collapse: collapse; font-size: 0.88rem;">
          <thead>
            <tr style="background: rgba(255,255,255,0.04); text-align: left;">
              <th style="padding: 10px 14px;">Evaluation Run</th>
              <th style="padding: 10px 14px;">Timestamp</th>
              <th style="padding: 10px 14px;">Total Score</th>
              <th style="padding: 10px 14px;">Classification</th>
            </tr>
          </thead>
          <tbody>${hRows}</tbody>
        </table>
      </div>
    `;
  } else if (tabName === 'gaps') {
    if (!latest || (!latest.skill_gaps && !latest.recommendations)) {
      bodyContent.innerHTML = `<p style="text-align: center; color: var(--text-muted); padding: 30px;">No skill gap analysis generated yet for this student.</p>`;
      return;
    }

    const prioOrder = { 'high': 1, 'mid': 2, 'medium': 2, 'low': 3 };
    let gapsHtml = (latest.skill_gaps || [])
      .filter(g => !g.category_name.toLowerCase().includes('hire') && !g.category_name.toLowerCase().includes('pitch'))
      .sort((a, b) => (prioOrder[(a.priority || '').toLowerCase()] || 99) - (prioOrder[(b.priority || '').toLowerCase()] || 99))
      .map(g => {
        const p = (g.priority || '').toLowerCase() === 'medium' ? 'Mid' : g.priority;
        return `
      <div style="background: rgba(248, 113, 113, 0.05); border: 1px solid rgba(248, 113, 113, 0.2); padding: 12px 16px; border-radius: 8px; margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; font-weight: 700; color: #f87171;">
          <span>🎯 ${g.category_name}</span>
          <span style="font-size: 0.8rem; background: rgba(248,113,113,0.2); padding: 2px 8px; border-radius: 4px;">Priority: ${p}</span>
        </div>
        <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: var(--text-secondary);">${g.gap_description}</p>
        <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: var(--text-muted);">Current: ${g.current_value} | Ideal Target: ${g.target_value}</p>
      </div>
    `;})
      .join('');

    let recsHtml = (latest.recommendations || [])
      .filter(r => !r.category_name.toLowerCase().includes('hire') && !r.category_name.toLowerCase().includes('pitch'))
      .sort((a, b) => (prioOrder[(a.priority || '').toLowerCase()] || 99) - (prioOrder[(b.priority || '').toLowerCase()] || 99))
      .map(r => `
      <div style="background: rgba(52, 211, 153, 0.05); border: 1px solid rgba(52, 211, 153, 0.2); padding: 12px 16px; border-radius: 8px; margin-bottom: 10px;">
        <div style="font-weight: 700; color: #34d399;">💡 ${r.category_name}</div>
        <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: var(--text-secondary);">${r.recommendation}</p>
      </div>
    `).join('');

    bodyContent.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <div>
          <h4 style="color: #f87171; margin-bottom: 12px; font-weight: 700;">Identified Skill Gaps</h4>
          ${gapsHtml || '<p style="color: var(--text-muted);">No critical skill gaps identified.</p>'}
        </div>
        <div>
          <h4 style="color: #34d399; margin-bottom: 12px; font-weight: 700;">Targeted Recommendations</h4>
          ${recsHtml || '<p style="color: var(--text-muted);">No recommendations available.</p>'}
        </div>
      </div>
    `;
  } else if (tabName === 'cards') {
    let acad = cardData.academics || {};
    let backlogs = cardData.backlogs || [];
    let langs = cardData.coding_languages || [];
    let tech = cardData.technical_skills || [];
    let platforms = cardData.coding_platforms || [];
    let linkedin = cardData.linkedin || {};
    let papers = cardData.research_papers || [];
    let internships = cardData.internships || [];
    let hackathons = cardData.hackathons || [];
    let certs = cardData.courses_certificates || [];
    let aptitude = cardData.aptitude || [];
    let comm = cardData.communication || [];
    let foreign = cardData.foreign_languages || [];
    let projects = cardData.projects || [];

    // Helper to check if a value represents "None" or "No" or is blank
    const isNoneOrNo = (val) => {
      if (val === null || val === undefined) return true;
      if (typeof val === 'boolean') return !val;
      if (typeof val === 'number') return val === 0;
      const s = String(val).trim().toUpperCase();
      return s === '' || s === 'NONE' || s === 'NO' || s === 'FALSE' || s === '0' || s === 'N/A';
    };

    const noBadgeHtml = `<p style="margin: 0; font-weight: 700; color: var(--text-muted); font-size: 0.92rem; letter-spacing: 0.05em;">NO</p>`;

    // 1. Academics & Backlogs
    let hasBacklogs = !isNoneOrNo(acad.previous_backlogs) || backlogs.length > 0;
    let backlogStatusText = hasBacklogs ? '<span style="color:#f87171; font-weight: 700;">⚠️ Yes</span>' : '<span style="color: var(--text-muted); font-weight: 700;">NO</span>';

    // 2. Coding Languages
    let validLangs = langs.filter(l => l && l.language_name && !isNoneOrNo(l.language_name));

    // 3. Technical Skills
    let validTech = tech.filter(t => t && t.skill_name && !isNoneOrNo(t.skill_name));

    // 4. Coding Platforms
    let validPlatforms = platforms.filter(p => p && p.platform_name && !isNoneOrNo(p.platform_name));

    // 5. LinkedIn Profile
    let hasLinkedin = linkedin && !isNoneOrNo(linkedin.uses_for_academic_purposes);

    // 6. Research Papers
    let hasPapers = papers.length > 0 && !isNoneOrNo(papers[0].has_published);
    let validPapers = papers.filter(rp => rp && rp.paper_title && !isNoneOrNo(rp.paper_title));
    if (!hasPapers) validPapers = [];

    // 7. Internships
    let hasInternships = internships.length > 0 && !isNoneOrNo(internships[0].has_internship);
    let validInternships = internships.filter(i => i && i.company_name && !isNoneOrNo(i.company_name));
    if (!hasInternships) validInternships = [];

    // 8. Hackathons
    let hasHackathons = hackathons.length > 0 && !isNoneOrNo(hackathons[0].has_hackathon);
    let validHackathons = hackathons.filter(h => h && h.hackathon_name && !isNoneOrNo(h.hackathon_name));
    if (!hasHackathons) validHackathons = [];

    // 9. Courses & Certificates
    let hasCerts = certs.length > 0 && !isNoneOrNo(certs[0].has_certificate);
    let validCerts = certs.filter(c => c && c.course_name && !isNoneOrNo(c.course_name));
    if (!hasCerts) validCerts = [];

    // 10. Aptitude
    let validAptitude = aptitude.filter(a => a && a.skill_name && !isNoneOrNo(a.skill_name));

    // 11. Communication
    let validComm = comm.filter(c => c && c.skill_name && !isNoneOrNo(c.skill_name));

    // 12. Foreign Languages
    let validForeign = foreign.filter(fl => fl && fl.language_name && !isNoneOrNo(fl.language_name));

    // 13. Projects
    let hasProjects = projects.length > 0 && !isNoneOrNo(projects[0].has_project);
    let validProjects = projects.filter(p => p && p.project_title && !isNoneOrNo(p.project_title));
    if (!hasProjects) validProjects = [];

    let sgpaList = [];
    for (let sem = 1; sem <= 8; sem++) {
      let val = acad[`semester_${sem}_sgpa`];
      if (val !== null && val !== undefined) {
        sgpaList.push(`Sem ${sem}: ${Number(val).toFixed(2)}`);
      }
    }
    let sgpaStr = sgpaList.length > 0 ? sgpaList.join(' | ') : 'No semester SGPAs recorded';

    // Collect academic marksheet documents
    let acadDocs = [];
    if (acad.marksheet_10th_path) {
      acadDocs.push({ label: '10th Marksheet', path: acad.marksheet_10th_path });
    }
    if (acad.marksheet_12th_path) {
      acadDocs.push({ label: '12th Marksheet', path: acad.marksheet_12th_path });
    }
    if (acad.marksheet_sems_json) {
      try {
        let semsObj = typeof acad.marksheet_sems_json === 'string' ? JSON.parse(acad.marksheet_sems_json) : acad.marksheet_sems_json;
        for (let [semKey, semPath] of Object.entries(semsObj)) {
          if (semPath) {
            // Keys can be numeric "1","2",... or named "semester_1"/"sem_1"
            let semNum = semKey.replace(/^semester_/i, '').replace(/^sem_/i, '');
            acadDocs.push({ label: `Sem ${semNum} Marksheet`, path: semPath });
          }
        }
      } catch(e) {}
    }

    bodyContent.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 18px;">

        <!-- 1. Academics -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 10px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">01</span> Academics &amp; Backlogs
          </h4>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px; margin-bottom: 10px;">
            <div style="background: rgba(255,255,255,0.03); border-radius: 7px; padding: 8px 12px; border: 1px solid rgba(255,255,255,0.05);">
              <p style="margin: 0; font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">10th Standard</p>
              <p style="margin: 4px 0 0 0; font-weight: 700; font-size: 1rem;">${acad.percentage_10th != null ? acad.percentage_10th + '%' : '—'}</p>
            </div>
            <div style="background: rgba(255,255,255,0.03); border-radius: 7px; padding: 8px 12px; border: 1px solid rgba(255,255,255,0.05);">
              <p style="margin: 0; font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">12th Standard</p>
              <p style="margin: 4px 0 0 0; font-weight: 700; font-size: 1rem;">${acad.percentage_12th != null ? acad.percentage_12th + '%' : '—'}</p>
            </div>
            <div style="background: rgba(255,255,255,0.03); border-radius: 7px; padding: 8px 12px; border: 1px solid rgba(255,255,255,0.05);">
              <p style="margin: 0; font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Previous Backlogs</p>
              <p style="margin: 4px 0 0 0; font-weight: 700; font-size: 0.88rem;">${backlogStatusText}</p>
            </div>
          </div>
          <p style="margin: 4px 0 10px 0; font-size: 0.82rem; color: var(--text-secondary);"><strong>Semester SGPAs:</strong> ${sgpaStr}</p>
          ${hasBacklogs && backlogs.length > 0 ? `<div style="background: rgba(248,113,113,0.06); border: 1px solid rgba(248,113,113,0.2); border-radius: 7px; padding: 8px 12px; margin-bottom: 10px; font-size: 0.82rem; color: #f87171;"><strong>Backlog Subjects:</strong> ${backlogs.map(b => b.subject_name + ' [' + b.academic_level + ']').join(', ')}</div>` : ''}
          ${acadDocs.length > 0 ? `
            <div>
              <p style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.06em;">📂 Uploaded Academic Documents (${acadDocs.length})</p>
              <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px;">
                ${acadDocs.map(d => renderAdminDocCard(d.label, d.path)).join('')}
              </div>
            </div>
          ` : '<p style="font-size: 0.82rem; color: var(--text-muted); margin: 0;">📂 No academic documents uploaded.</p>'}
        </div>

        <!-- 2. Coding Languages -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 10px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">02</span> Coding Languages
          </h4>
          ${validLangs.length === 0 ? noBadgeHtml : `
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
              ${validLangs.map(l => `<span style="background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.3); padding: 5px 12px; border-radius: 6px; font-size: 0.82rem; color: var(--text-primary); font-weight: 600;">${l.language_name || 'Language'} <span style="font-weight: 400; opacity: 0.7;">(${l.proficiency_level || 'N/A'})</span></span>`).join('')}
            </div>
          `}
        </div>

        <!-- 3. Technical Skills -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 10px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">03</span> Technical Skills
          </h4>
          ${validTech.length === 0 ? noBadgeHtml : `
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
              ${validTech.map(t => `<span style="background: rgba(139,92,246,0.12); border: 1px solid rgba(139,92,246,0.3); padding: 5px 12px; border-radius: 6px; font-size: 0.82rem; color: var(--text-primary); font-weight: 600;">${t.skill_name || 'Skill'} <span style="font-weight: 400; opacity: 0.7;">(${t.proficiency_level || 'N/A'})</span></span>`).join('')}
            </div>
          `}
        </div>

        <!-- 4. Coding Platforms -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 10px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">04</span> Coding Platforms
          </h4>
          ${validPlatforms.length === 0 ? noBadgeHtml : `
            <div style="display: flex; flex-direction: column; gap: 8px;">
              ${validPlatforms.map(p => `<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 7px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;"><div><p style="margin: 0; font-weight: 700; font-size: 0.88rem;">${p.platform_name || 'Platform'}</p><p style="margin: 2px 0 0 0; font-size: 0.8rem; color: var(--text-muted);">${p.questions_solved || 0} questions solved</p></div>${p.profile_url ? `<a href="${p.profile_url}" target="_blank" style="font-size: 0.78rem; color: #38bdf8; font-weight: 600; text-decoration: none; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.25); padding: 4px 10px; border-radius: 5px; white-space: nowrap;">🔗 Profile</a>` : ''}</div>`).join('')}
            </div>
          `}
        </div>

        <!-- 5. LinkedIn Profile -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 10px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">05</span> LinkedIn Profile
          </h4>
          ${!hasLinkedin ? noBadgeHtml : `
            <div style="display: flex; flex-wrap: wrap; gap: 16px; align-items: center;">
              <div><p style="margin: 0; font-size: 0.82rem; color: var(--text-muted);">Academic Use</p><p style="margin: 3px 0 0 0; font-weight: 700;"><span style="color:#34d399;">✓ Yes</span></p></div>
              <div><p style="margin: 0; font-size: 0.82rem; color: var(--text-muted);">Posts Count</p><p style="margin: 3px 0 0 0; font-weight: 700;">${linkedin.number_of_posts || 0}</p></div>
              ${linkedin.profile_url ? `<a href="${linkedin.profile_url}" target="_blank" style="font-size: 0.82rem; color: #38bdf8; font-weight: 600; text-decoration: none; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.25); padding: 6px 14px; border-radius: 6px;">🔗 Open LinkedIn Profile</a>` : ''}
            </div>
          `}
        </div>

        <!-- 6. Research Papers -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 12px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">06</span> Research Papers
          </h4>
          ${validPapers.length === 0 ? noBadgeHtml : validPapers.map((rp, idx) => `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 14px; margin-bottom: 10px;">
              <p style="margin: 0 0 4px 0; font-size: 0.88rem; font-weight: 700; color: var(--text-primary);">📄 ${rp.paper_title || 'Untitled Paper'}</p>
              <p style="margin: 2px 0; font-size: 0.8rem; color: var(--text-secondary);">📚 ${rp.publication_name || 'N/A'} ${rp.publication_date ? '&nbsp;|&nbsp; 📅 ' + rp.publication_date : ''}</p>
              <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; align-items: flex-start;">
                ${rp.paper_url ? `<a href="${rp.paper_url}" target="_blank" style="font-size: 0.78rem; color: #38bdf8; font-weight: 600; text-decoration: none; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.25); padding: 4px 10px; border-radius: 5px; white-space: nowrap; align-self: flex-start;">🔗 View Paper</a>` : ''}
                ${rp.document_path ? renderAdminDocCard('Research Document', rp.document_path) : '<span style="font-size: 0.76rem; color: var(--text-muted); align-self: center;">No document uploaded</span>'}
              </div>
            </div>
          `).join('')}
        </div>

        <!-- 7. Internships -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 12px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">07</span> Internships
          </h4>
          ${validInternships.length === 0 ? noBadgeHtml : validInternships.map((i, idx) => `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 14px; margin-bottom: 10px;">
              <p style="margin: 0 0 2px 0; font-size: 0.88rem; font-weight: 700;">🏢 ${i.company_name || 'Company'}</p>
              <p style="margin: 2px 0; font-size: 0.8rem; color: var(--text-secondary);">💼 Role: <strong>${i.role || 'Intern'}</strong> &nbsp;|&nbsp; 📅 ${i.start_date || 'N/A'} → ${i.end_date || 'Present'}</p>
              <div style="margin-top: 10px;">
                ${i.offer_letter_path ? renderAdminDocCard('Offer Letter', i.offer_letter_path) : '<span style="font-size: 0.76rem; color: var(--text-muted);">No offer letter uploaded</span>'}
              </div>
            </div>
          `).join('')}
        </div>

        <!-- 8. Hackathons -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 12px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">08</span> Hackathons
          </h4>
          ${validHackathons.length === 0 ? noBadgeHtml : validHackathons.map((h, idx) => `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 14px; margin-bottom: 10px;">
              <p style="margin: 0 0 2px 0; font-size: 0.88rem; font-weight: 700;">🏆 ${h.hackathon_name || 'Hackathon'}</p>
              <p style="margin: 2px 0; font-size: 0.8rem; color: var(--text-secondary);">🗂️ Organizer: ${h.organizer || 'N/A'} &nbsp;|&nbsp; 🎯 Position: <span style="font-weight: 700; color: #fbbf24;">${h.position || 'Participant'}</span></p>
              <div style="margin-top: 10px;">
                ${h.certificate_path ? renderAdminDocCard('Certificate', h.certificate_path) : '<span style="font-size: 0.76rem; color: var(--text-muted);">No certificate uploaded</span>'}
              </div>
            </div>
          `).join('')}
        </div>

        <!-- 9. Courses & Certificates -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 12px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">09</span> Courses &amp; Certificates
          </h4>
          ${validCerts.length === 0 ? noBadgeHtml : validCerts.map((c, idx) => `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 14px; margin-bottom: 10px;">
              <p style="margin: 0 0 2px 0; font-size: 0.88rem; font-weight: 700;">🎓 ${c.course_name || 'Course'}</p>
              <p style="margin: 2px 0; font-size: 0.8rem; color: var(--text-secondary);">🏫 Platform: ${c.platform || 'N/A'} ${c.completion_date ? '&nbsp;|&nbsp; ✅ Completed: ' + c.completion_date : ''}</p>
              <div style="margin-top: 10px;">
                ${c.certificate_path ? renderAdminDocCard('Certificate', c.certificate_path) : '<span style="font-size: 0.76rem; color: var(--text-muted);">No certificate uploaded</span>'}
              </div>
            </div>
          `).join('')}
        </div>

        <!-- 10. Aptitude Skills -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 10px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">10</span> Aptitude Ratings
          </h4>
          ${validAptitude.length === 0 ? noBadgeHtml : `
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
              ${validAptitude.map(a => `<span style="background: rgba(234,179,8,0.12); border: 1px solid rgba(234,179,8,0.3); padding: 5px 12px; border-radius: 6px; font-size: 0.82rem; color: var(--text-primary); font-weight: 600;">${a.skill_name || 'Aptitude'}: <span style="color: #fbbf24;">${a.proficiency_level || 'N/A'}</span></span>`).join('')}
            </div>
          `}
        </div>

        <!-- 11. Communication Skills -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 10px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">11</span> Communication Ratings
          </h4>
          ${validComm.length === 0 ? noBadgeHtml : `
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
              ${validComm.map(c => `<span style="background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); padding: 5px 12px; border-radius: 6px; font-size: 0.82rem; color: var(--text-primary); font-weight: 600;">${c.skill_name || 'Communication'}: <span style="color: #34d399;">${c.proficiency_level || 'N/A'}</span></span>`).join('')}
            </div>
          `}
        </div>

        <!-- 12. Foreign Languages -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 10px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">12</span> Foreign Languages
          </h4>
          ${validForeign.length === 0 ? noBadgeHtml : `
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
              ${validForeign.map(fl => `<span style="background: rgba(6,182,212,0.12); border: 1px solid rgba(6,182,212,0.3); padding: 5px 12px; border-radius: 6px; font-size: 0.82rem; color: var(--text-primary); font-weight: 600;">${fl.language_name || 'Language'} <span style="font-weight: 400; opacity: 0.7;">(${fl.proficiency_level || 'N/A'})</span></span>`).join('')}
            </div>
          `}
        </div>

        <!-- 13. Projects -->
        <div style="background: rgba(56,81,68,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
          <h4 style="color: var(--accent-primary); margin: 0 0 12px 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
            <span style="background: rgba(56,81,68,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em;">13</span> Projects
          </h4>
          ${validProjects.length === 0 ? noBadgeHtml : validProjects.map(p => {
            let lList = [];
            if (p.languages_json) {
              try { lList = typeof p.languages_json === 'string' ? JSON.parse(p.languages_json) : p.languages_json; } catch(e){}
            }
            return `
              <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); padding: 12px 14px; border-radius: 8px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; flex-wrap: wrap;">
                  <strong style="color: var(--text-primary); font-size: 0.9rem;">🚀 ${p.project_title || 'Project'}</strong>
                  ${p.github_url ? `<a href="${p.github_url}" target="_blank" style="font-size: 0.76rem; color: #38bdf8; font-weight: 600; text-decoration: none; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.25); padding: 3px 10px; border-radius: 5px; white-space: nowrap;">💻 GitHub</a>` : ''}
                </div>
                <p style="margin: 6px 0 0 0; font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5;">${p.project_description || 'No description provided.'}</p>
                ${lList && lList.length > 0 ? `<div style="margin-top: 6px; display: flex; flex-wrap: wrap; gap: 5px;">${lList.map(lang => `<span style="font-size: 0.72rem; background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2); padding: 2px 7px; border-radius: 4px; color: var(--text-muted);">${lang}</span>`).join('')}</div>` : ''}
              </div>
            `;
          }).join('')}
        </div>

      </div>

      <!-- Admin Document Lightbox -->
      <div id="admin-doc-lightbox" onclick="closeAdminDocLightbox()" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.88); z-index:99999; align-items:center; justify-content:center; flex-direction:column; padding:20px;">
        <div onclick="event.stopPropagation()" style="background: var(--bg-card,#1a1f2e); border-radius: 14px; border: 1px solid rgba(255,255,255,0.1); max-width: 90vw; max-height: 90vh; width: 860px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 25px 60px rgba(0,0,0,0.6);">
          <div style="padding: 14px 18px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; justify-content: space-between; align-items: center;">
            <p id="admin-doc-lightbox-title" style="margin: 0; font-weight: 700; font-size: 0.95rem; color: var(--text-primary);">Document Viewer</p>
            <div style="display: flex; gap: 10px; align-items: center;">
              <a id="admin-doc-lightbox-open" href="#" target="_blank" style="font-size: 0.78rem; color: #38bdf8; font-weight: 600; text-decoration: none; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.25); padding: 4px 12px; border-radius: 5px;">↗ Open in New Tab</a>
              <button onclick="closeAdminDocLightbox()" style="background: rgba(255,255,255,0.08); border: none; color: var(--text-muted); font-size: 1.4rem; cursor: pointer; width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; line-height: 1;">&times;</button>
            </div>
          </div>
          <div id="admin-doc-lightbox-body" style="flex: 1; overflow: auto; display: flex; align-items: center; justify-content: center; min-height: 400px; background: rgba(0,0,0,0.2);">
            <!-- Content injected by JS -->
          </div>
        </div>
      </div>
    `;
  }

}
