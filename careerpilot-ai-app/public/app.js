// Navigation Tabs
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const target = btn.getAttribute('data-tab');
    document.getElementById(target).classList.add('active');
  });
});

function copyContent(id) {
  const el = document.getElementById(id);
  const text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    alert('Copied to clipboard!');
  });
}

// Prompt Shortcuts
function setChatPrompt(t) {
  const input = document.getElementById('chatInput');
  input.value = t;
  input.focus();
}

function setCoachPrompt(t) {
  const input = document.getElementById('coachInput');
  input.value = t;
  input.focus();
}

// 1. Send Chat
async function sendChat() {
  const input = document.getElementById('chatInput');
  const query = input.value.trim();
  if (!query) return;

  const btnLabel = document.getElementById('chatBtnLabel');
  const spinner = document.getElementById('chatSpinner');
  const card = document.getElementById('chatResultCard');
  const output = document.getElementById('chatOutput');

  btnLabel.textContent = 'Thinking...';
  spinner.classList.remove('hidden');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const d = await res.json();
    if (!res.ok) throw new Error(d.detail || 'Inquiry error');
    output.textContent = d.response;
    card.classList.remove('hidden');
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    btnLabel.textContent = 'Send Inquiry';
    spinner.classList.add('hidden');
  }
}

// 2. Analyze JD
async function analyzeJd() {
  const input = document.getElementById('jdInput');
  const job_description = input.value.trim();
  if (!job_description) {
    alert('Please paste a job description.');
    return;
  }

  const btnLabel = document.getElementById('jdBtnLabel');
  const spinner = document.getElementById('jdSpinner');
  const resultArea = document.getElementById('jdResultArea');

  btnLabel.textContent = 'Scanning ATS keywords...';
  spinner.classList.remove('hidden');

  try {
    const res = await fetch('/api/analyze-jd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_description })
    });
    const d = await res.json();
    if (!res.ok) throw new Error(d.detail || 'Analysis error');

    document.getElementById('matchRateVal').textContent = `${d.match_percentage}%`;
    document.getElementById('detectedCount').textContent = d.total_skills_count;

    const matchedContainer = document.getElementById('matchedSkillsTags');
    matchedContainer.innerHTML = d.matching_skills.length
      ? d.matching_skills.map(s => `<span class="skill-tag skill-matched">✓ ${s}</span>`).join('')
      : '<span style="color:var(--text-dim); font-size:0.85rem;">No exact candidate skill overlaps detected.</span>';

    const missingContainer = document.getElementById('missingSkillsTags');
    missingContainer.innerHTML = d.missing_skills.length
      ? d.missing_skills.map(s => `<span class="skill-tag skill-missing">+ ${s}</span>`).join('')
      : '<span style="color:var(--text-dim); font-size:0.85rem;">All detected skills matched!</span>';

    document.getElementById('jdAdviceOutput').textContent = d.advice;
    resultArea.classList.remove('hidden');
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    btnLabel.textContent = 'Analyze Job Description';
    spinner.classList.add('hidden');
  }
}

// 3. Mock Interview
let currentSelectedQuestion = '';

async function startInterview() {
  const role = document.getElementById('interviewRole').value.trim() || 'Software Engineer';
  const btnLabel = document.getElementById('interviewBtnLabel');
  const spinner = document.getElementById('interviewSpinner');
  const area = document.getElementById('questionListArea');
  const container = document.getElementById('questionsContainer');

  btnLabel.textContent = 'Generating...';
  spinner.classList.remove('hidden');

  try {
    const res = await fetch('/api/mock-interview/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role })
    });
    const d = await res.json();
    if (!res.ok) throw new Error(d.detail || 'Interview generation error');

    container.innerHTML = '';
    d.questions.forEach((q, idx) => {
      const item = document.createElement('div');
      item.className = 'question-item';
      item.textContent = `${idx + 1}. ${q}`;
      item.onclick = () => selectQuestion(q, item);
      container.appendChild(item);
    });

    if (d.questions.length > 0) {
      selectQuestion(d.questions[0], container.children[0]);
    }

    area.classList.remove('hidden');
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    btnLabel.textContent = 'Generate Questions';
    spinner.classList.add('hidden');
  }
}

function selectQuestion(q, elem) {
  currentSelectedQuestion = q;
  document.querySelectorAll('.question-item').forEach(el => el.classList.remove('selected'));
  if (elem) elem.classList.add('selected');
}

async function evaluateAnswer() {
  const answer = document.getElementById('userAnswerInput').value.trim();
  if (!currentSelectedQuestion) {
    alert('Please select a question first.');
    return;
  }
  if (!answer) {
    alert('Please enter your answer to evaluate.');
    return;
  }

  const btnLabel = document.getElementById('evalBtnLabel');
  const spinner = document.getElementById('evalSpinner');
  const card = document.getElementById('evalResultCard');
  const output = document.getElementById('evalOutput');

  btnLabel.textContent = 'Critiquing...';
  spinner.classList.remove('hidden');

  try {
    const res = await fetch('/api/mock-interview/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: currentSelectedQuestion, answer })
    });
    const d = await res.json();
    if (!res.ok) throw new Error(d.detail || 'Critique error');

    output.textContent = d.evaluation;
    card.classList.remove('hidden');
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    btnLabel.textContent = 'Submit Answer for Critique';
    spinner.classList.add('hidden');
  }
}

// 4. Career Coach
async function sendCoach() {
  const input = document.getElementById('coachInput');
  const question = input.value.trim();
  if (!question) return;

  const btnLabel = document.getElementById('coachBtnLabel');
  const spinner = document.getElementById('coachSpinner');
  const card = document.getElementById('coachResultCard');
  const output = document.getElementById('coachOutput');

  btnLabel.textContent = 'Formulating Strategy...';
  spinner.classList.remove('hidden');

  try {
    const res = await fetch('/api/career-coach', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const d = await res.json();
    if (!res.ok) throw new Error(d.detail || 'Coaching error');

    output.textContent = d.coaching;
    card.classList.remove('hidden');
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    btnLabel.textContent = 'Get Coaching Plan';
    spinner.classList.add('hidden');
  }
}
