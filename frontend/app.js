const form = document.querySelector('#scan-form');
const button = document.querySelector('#scan-btn');
const statusBox = document.querySelector('#status');
const results = document.querySelector('#results');
let latestFindings = [];

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const url = document.querySelector('#url').value.trim();
  button.disabled = true;
  button.textContent = 'Scanning…';
  results.classList.add('hidden');
  statusBox.classList.remove('hidden');
  statusBox.textContent = 'Checking the website. This can take a little while…';
  try {
    const response = await fetch('/api/scan', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({url, max_pages: 10})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not scan this website.');
    latestFindings = data.findings || [];
    render(data);
    statusBox.classList.add('hidden');
    results.classList.remove('hidden');
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    button.disabled = false;
    button.innerHTML = 'Scan website <span>→</span>';
  }
});

function render(data) {
  document.querySelector('#scanned-url').textContent = data.scanned_url;
  document.querySelector('#pages-count').textContent = data.pages_scanned;
  document.querySelector('#findings-count').textContent = data.findings_count;
  document.querySelector('#high-count').textContent = data.findings.filter(x => x.severity === 'high').length;
  document.querySelector('#notice').textContent = data.notice;
  const list = document.querySelector('#finding-list');
  list.innerHTML = '';
  if (!data.findings.length) {
    list.innerHTML = '<div class="finding"><h3>No findings in the checks performed</h3><p>This does not guarantee that the website has no issues.</p></div>';
    return;
  }
  data.findings.forEach(item => {
    const card = document.createElement('article');
    card.className = 'finding';
    const top = document.createElement('div'); top.className = 'finding-top';
    const heading = document.createElement('h3'); heading.textContent = label(item.category);
    const severity = document.createElement('span'); severity.className = `severity ${item.severity}`; severity.textContent = item.severity;
    top.append(heading, severity);
    const url = document.createElement('p'); url.textContent = item.url;
    const evidence = document.createElement('p'); evidence.textContent = `Evidence: ${item.evidence}`;
    const fix = document.createElement('p'); fix.textContent = `Suggested fix: ${item.suggested_fix}`;
    card.append(top, url, evidence, fix); list.append(card);
  });
}
function label(value) {
  return ({page_response:'Page response issue',missing_title:'Missing page title',missing_meta_description:'Missing meta description',missing_image_alt:'Image missing alt attribute'})[value] || value;
}
document.querySelector('#export-btn').addEventListener('click', () => {
  const rows = [['category','severity','url','evidence','suggested_fix'], ...latestFindings.map(x => [x.category,x.severity,x.url,x.evidence,x.suggested_fix])];
  const csv = rows.map(row => row.map(value => `"${String(value ?? '').replaceAll('"','""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'});
  const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'buglens-report.csv'; link.click();
  URL.revokeObjectURL(link.href);
});
