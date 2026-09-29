const $ = id => document.getElementById(id);
let lastResult = null;
const make = (tag, text, className) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (className) node.className = className; return node; };
const examples = {
  refund: { question: 'What is the refund policy?', correction: false },
  correction: { question: 'Does Northstar Academy guarantee a job or salary?', correction: true },
  unknown: { question: 'What is the lunar observatory telescope diameter?', correction: false }
};
document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
  const example = examples[button.dataset.example]; $('question').value = example.question; $('correction-demo').checked = example.correction; $('question').focus();
}));
$('mode').addEventListener('change', () => {
  $('mode-note').textContent = $('mode').value === 'live' ? 'Calls EURI using the server’s local key. A run can take several minutes; each stage uses your API quota.' : 'Deterministic sample demo. No model calls or API charges.';
});
$('max-retries').addEventListener('change', () => { $('attempt-limit').textContent = Number($('max-retries').value) + 1; });

async function readJson(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check the question and run settings.');
  return data;
}
async function init() {
  try {
    const [health, corpus] = await Promise.all([readJson('/api/health'), readJson('/api/documents')]);
    $('connection').textContent = health.live_configured ? 'EURI key configured' : 'Offline demo ready';
    $('model-name').textContent = health.model;
    $('doc-count').textContent = corpus.documents.length;
    for (const doc of corpus.documents) {
      const details = make('details', undefined, 'document'); details.id = 'doc-' + doc.id;
      const summary = make('summary'), title = make('span', doc.title); title.append(make('small', doc.id + ' · sample policy'));
      summary.append(title); details.append(summary, make('p', doc.text)); $('documents').append(details);
    }
  } catch (error) { $('connection').textContent = 'Connection unavailable'; showError(error.message); }
}
function showError(message) { $('error').textContent = message; $('error').classList.remove('hidden'); }
function details(label, content) { const node = make('details'); node.append(make('summary', label), make('pre', typeof content === 'string' ? content : JSON.stringify(content, null, 2))); return node; }
function stage(label, message, extra) { const node = make('div', undefined, 'stage-item'); node.append(make('b', label), make('p', message)); if (extra) node.append(extra); return node; }
function render(result) {
  lastResult = result;
  const accepted = result.status === 'accepted';
  $('answer-empty').classList.add('hidden'); $('answer-content').classList.remove('hidden');
  $('answer-text').textContent = result.answer;
  $('answer-badge').textContent = accepted ? 'EVALUATION PASSED' : 'INSUFFICIENT EVIDENCE';
  $('answer-badge').className = 'tag ' + (accepted ? 'good' : 'bad');
  $('answer-meta').textContent = `${result.mode === 'demo' ? 'Offline demo' : result.model} · ${(result.duration_ms / 1000).toFixed(2)}s · ${result.retries_used} retries`;
  $('sources').replaceChildren();
  for (const source of result.sources) { const link = make('a', '▤ ' + source.title, 'source-chip'); link.href = '#doc-' + source.id; link.onclick = () => { const doc = $('doc-' + source.id); if (doc) doc.open = true; }; $('sources').append(link); }
  $('metric-attempts').textContent = result.attempt_count;
  const evaluation = result.attempts.at(-1)?.evaluation;
  $('metric-relevance').textContent = evaluation ? Math.round(evaluation.answer_relevance * 100) + '%' : '—';
  $('metric-grounding').textContent = evaluation ? Math.round(evaluation.grounding * 100) + '%' : '—';
  $('trace-badge').textContent = accepted ? 'COMPLETED' : 'LIMIT REACHED';
  $('activity').replaceChildren();
  for (const attempt of result.attempts) {
    const block = make('article', undefined, 'attempt-block');
    const header = make('div', undefined, 'attempt-header'); header.append(make('b', `Attempt ${attempt.number}`), make('span', attempt.accepted ? 'ACCEPTED' : attempt.rewrite ? 'RETRY' : 'REJECTED', 'tag ' + (attempt.accepted ? 'good' : 'bad'))); block.append(header);
    block.append(stage('01 / Retrieve', `${attempt.retrieved.length} documents · ${attempt.query}`, details('Inspect retrieved context', attempt.retrieved)));
    block.append(stage('02 / Grade documents', `${attempt.kept_ids.length} relevant documents retained`, details('Inspect relevance grades', attempt.grades)));
    if (attempt.draft) {
      if (attempt.injected_draft) block.append(make('p', 'Teaching fault: one deliberately unsupported draft was inserted.', 'injection-note'));
      block.append(stage('03 / Generate', 'Draft created from the retained context' + (attempt.injected_draft ? ', then replaced by the teaching fault.' : '.'), details('Inspect draft', attempt.draft)));
      block.append(stage('04 / Evaluate answer', attempt.evaluation.feedback, details('Inspect evaluation & citations', attempt.evaluation)));
    } else block.append(stage('04 / Evidence check', 'No relevant context. Generation was skipped.'));
    if (attempt.rewrite) block.append(stage('↻ / Rewrite & retrieve again', attempt.rewrite));
    $('activity').append(block);
  }
}
$('query-form').addEventListener('submit', async event => {
  event.preventDefault(); $('error').classList.add('hidden');
  const request = {question: $('question').value.trim(), mode: $('mode').value, max_retries: Number($('max-retries').value), correction_demo: $('correction-demo').checked};
  const controls = [...document.querySelectorAll('#query-form input, #query-form select, #query-form textarea, #query-form button')]; controls.forEach(node => { node.disabled = true; });
  $('run-button').textContent = 'Running…'; $('trace-badge').textContent = 'RUNNING';
  $('activity').replaceChildren(make('p', request.mode === 'live' ? 'Running retrieval and EURI evaluation. The completed trace will appear here.' : 'Running the offline demonstration…', 'pending'));
  $('answer-content').classList.add('hidden'); $('answer-empty').classList.remove('hidden'); $('answer-badge').textContent = 'CHECKING EVIDENCE'; $('answer-badge').className = 'tag';
  ['metric-attempts', 'metric-relevance', 'metric-grounding'].forEach(id => { $(id).textContent = '—'; }); lastResult = null;
  try { render(await readJson('/api/query', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(request)})); }
  catch (error) { showError(error.message); $('trace-badge').textContent = 'ERROR'; $('activity').replaceChildren(make('p', 'The run failed. No answer was accepted. Check the error and retry.')); $('answer-badge').textContent = 'RUN FAILED'; }
  finally { controls.forEach(node => { node.disabled = false; }); $('run-button').replaceChildren(document.createTextNode('Run Self-RAG '), make('span', '↗')); }
});
$('download').addEventListener('click', () => {
  if (!lastResult) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(lastResult, null, 2)], {type: 'application/json'}));
  const anchor = make('a'); anchor.href = url; anchor.download = 'self-rag-trace.json'; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
init();
