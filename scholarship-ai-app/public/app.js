// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    const target = btn.getAttribute('data-tab');
    document.getElementById(target).classList.add('active');
  });
});

// Quick Question Helper
function setQuery(text) {
  const input = document.getElementById('chatInput');
  input.value = text;
  input.focus();
}

// Range formatters
function updateIncome(val) {
  const num = parseInt(val, 10);
  document.getElementById('incomeVal').textContent = `₹${num.toLocaleString('en-IN')}`;
}

function updateMarks(val) {
  document.getElementById('marksVal').textContent = `${parseFloat(val).toFixed(1)}%`;
}

// Copy to Clipboard
function copyText(elementId) {
  const el = document.getElementById(elementId);
  const text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    alert('Copied to clipboard!');
  });
}

// Submit Chat Question
async function submitChat() {
  const input = document.getElementById('chatInput');
  const query = input.value.trim();
  if (!query) {
    alert('Please enter a question.');
    return;
  }

  const btnText = document.getElementById('askBtnText');
  const spinner = document.getElementById('askSpinner');
  const responseArea = document.getElementById('chatResponseArea');
  const answerEl = document.getElementById('chatAnswer');
  const sourcesEl = document.getElementById('chatSources');

  btnText.textContent = 'Analyzing...';
  spinner.classList.remove('hidden');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to fetch answer.');

    answerEl.textContent = data.answer;
    if (data.sources && data.sources.length > 0) {
      sourcesEl.innerHTML = `<strong>Source Reference:</strong> ${data.sources[0].snippet}`;
    } else {
      sourcesEl.innerHTML = '';
    }
    responseArea.classList.remove('hidden');
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    btnText.textContent = 'Ask AI Assistant';
    spinner.classList.add('hidden');
  }
}

// Submit Calculator
async function submitCalc() {
  const degree = document.getElementById('degreeSelect').value;
  const annual_income = parseFloat(document.getElementById('incomeRange').value);
  const marks_percentage = parseFloat(document.getElementById('marksRange').value);
  const course_years = parseInt(document.querySelector('input[name="courseYears"]:checked').value, 10);

  const selected_documents = [];
  if (document.getElementById('docIncome').checked) selected_documents.push('Income Certificate');
  if (document.getElementById('docAadhaar').checked) selected_documents.push('Aadhaar Card');
  if (document.getElementById('docPassbook').checked) selected_documents.push('Bank Passbook');
  if (document.getElementById('docMarksheet').checked) selected_documents.push('Marksheet');

  const emptyState = document.getElementById('calcEmptyState');
  const resultsContent = document.getElementById('calcResultContent');

  try {
    const res = await fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ degree, annual_income, marks_percentage, course_years, selected_documents })
    });

    const d = await res.json();
    if (!res.ok) throw new Error(d.detail || 'Calculation error');

    let statusPillClass = 'status-eligible';
    let statusText = '✅ Fully Eligible for Scholarship 2025';
    if (d.status === 'INELIGIBLE') {
      statusPillClass = 'status-ineligible';
      statusText = '❌ Currently Ineligible';
    } else if (d.status === 'PARTIALLY_ELIGIBLE') {
      statusPillClass = 'status-partial';
      statusText = '⚠️ Partially Eligible (Criteria Review Needed)';
    }

    resultsContent.innerHTML = `
      <div class="status-pill ${statusPillClass}">${statusText}</div>

      <div class="metrics-box">
        <span style="font-size:0.85rem; color:var(--text-dim); text-transform:uppercase; font-weight:700;">Total Estimated Aid</span>
        <div class="grant-highlight">₹${d.total_grant.toLocaleString('en-IN')}</div>
        <div class="breakdown-row">
          <span>Tuition Support (₹10,000 × ${d.semesters} sems)</span>
          <strong>₹${d.tuition_total.toLocaleString('en-IN')}</strong>
        </div>
        <div class="breakdown-row">
          <span>Book Allowance (₹3,000 × ${d.course_years} yrs)</span>
          <strong>₹${d.books_total.toLocaleString('en-IN')}</strong>
        </div>
      </div>

      <div class="metrics-box">
        <h4 style="font-family:var(--font-heading); margin-bottom:8px;">Criteria Breakdown</h4>
        <div class="check-item">${d.is_undergrad ? '✅' : '❌'} Degree: ${degree} (${d.is_undergrad ? 'Passed' : 'Must be Undergraduate'})</div>
        <div class="check-item">${d.income_pass ? '✅' : '❌'} Family Income: ₹${annual_income.toLocaleString('en-IN')} (${d.income_pass ? 'Under ₹6L limit' : 'Exceeds ₹6L'})</div>
        <div class="check-item">${d.marks_pass ? '✅' : '❌'} Marks: ${marks_percentage}% (${d.marks_pass ? 'Meets ≥ 60% requirement' : 'Below 60%'})</div>
      </div>

      <div class="metrics-box">
        <h4 style="font-family:var(--font-heading); margin-bottom:8px;">Document Readiness (${d.completed_docs.length}/4)</h4>
        ${d.completed_docs.map(doc => `<div class="check-item">✅ ${doc} ready</div>`).join('')}
        ${d.missing_docs.map(doc => `<div class="check-item" style="color:var(--accent-rose)">❌ ${doc} missing (required before applying)</div>`).join('')}
      </div>

      <div style="margin-top:16px;">
        <a href="${d.portal_url}" target="_blank" class="btn btn-primary btn-block" style="text-decoration:none;">
          Apply on NSP Portal (Deadline: ${d.deadline})
        </a>
      </div>
    `;

    emptyState.classList.add('hidden');
    resultsContent.classList.remove('hidden');
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

// Submit SOP
async function submitSop() {
  const student_name = document.getElementById('sopName').value.trim();
  const course_name = document.getElementById('sopCourse').value.trim();
  const financial_background = document.getElementById('sopBackground').value.trim();
  const career_goals = document.getElementById('sopGoals').value.trim();
  const tone = document.getElementById('sopTone').value;

  const btnText = document.getElementById('sopBtnText');
  const spinner = document.getElementById('sopSpinner');
  const emptyState = document.getElementById('sopEmpty');
  const outputEl = document.getElementById('sopOutput');
  const copyBtn = document.getElementById('sopCopyBtn');

  btnText.textContent = 'Drafting Statement of Purpose...';
  spinner.classList.remove('hidden');

  try {
    const res = await fetch('/api/generate-sop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_name, course_name, financial_background, career_goals, tone })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to generate SOP.');

    outputEl.textContent = data.sop;
    emptyState.classList.add('hidden');
    outputEl.classList.remove('hidden');
    copyBtn.disabled = false;
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    btnText.textContent = 'Generate Statement of Purpose';
    spinner.classList.add('hidden');
  }
}
