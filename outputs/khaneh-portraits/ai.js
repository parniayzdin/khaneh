(() => {
  const host = location.hostname === 'localhost' ? 'localhost' : '127.0.0.1';
  const api = `http://${host}:8082`;
  const section = document.createElement('section');
  section.className = 'archive-questions';
  section.setAttribute('aria-labelledby', 'askTitle');
  section.innerHTML = `<p class="eyebrow">EXPLORE THEIR STORIES</p>
    <h2 id="askTitle">Ask the archive.</h2>
    <p>Find answers in the biographies and researched source notes. Answers include their sources.</p>
    <form id="askForm">
      <label for="askPerson">About whom?</label>
      <select id="askPerson"><option value="">Anyone in the archive</option></select>
      <label for="askQuestion">Your question (English)</label>
      <div class="ask-input-row"><input id="askQuestion" required minlength="2" maxlength="300" placeholder="When did Nika join the protests?" autocomplete="off"><button type="submit">Ask</button></div>
    </form>
    <div class="ask-examples"><button type="button">Who loved football?</button><button type="button">When did Nika join the protests?</button></div>
    <div id="askResult" role="status" aria-live="polite" aria-atomic="true"></div>
    <p class="ask-scope">AI selects a supporting passage from this archive. It can miss an answer; this is not a live web search.</p>`;
  document.querySelector('.closing-note').before(section);
  const form = section.querySelector('form');
  const question = section.querySelector('#askQuestion');
  const person = section.querySelector('#askPerson');
  const result = section.querySelector('#askResult');
  const submit = form.querySelector('button');
  let busy = false;

  fetch(`${api}/api/people`, {signal: AbortSignal.timeout(8000)})
    .then(r => { if (!r.ok) throw Error('Archive unavailable'); return r.json(); })
    .then(people => people.forEach(p => {
      const option = document.createElement('option'); option.value = p.id;
      option.textContent = p.name; person.append(option);
    })).catch(() => { person.disabled = true; });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || question.value.trim().length < 2) return;
    busy = true; submit.disabled = true; submit.textContent = 'Looking…';
    result.textContent = 'Looking through the archive…';
    try {
      const params = new URLSearchParams({q: question.value.trim(), person_id: person.value});
      const response = await fetch(`${api}/api/ask?${params}`, {signal: AbortSignal.timeout(30000)});
      const data = await response.json();
      if (!response.ok) throw Error(data.error || 'The question could not be answered. Please try again.');
      if (typeof data.answer !== 'string' || !Array.isArray(data.sources)) throw Error('The answer could not be loaded. Please try again.');
      result.replaceChildren();
      const answer = document.createElement('p'); answer.textContent = data.answer.replace(/[-\u2010-\u2015]/g, ' '); result.append(answer);
      if (data.status === 'answered') {
        const label = document.createElement('strong'); label.textContent = 'Supporting sources'; result.append(label);
        const list = document.createElement('ul');
        data.sources.forEach(source => {
          const url = new URL(source.url);
          if (url.protocol !== 'https:') return;
          const item = document.createElement('li'), link = document.createElement('a');
          link.href = url.href; link.textContent = source.title.replace(/[-\u2010-\u2015]/g, ' ');
          link.target = '_blank'; link.rel = 'noopener noreferrer'; item.append(link); list.append(item);
        });
        result.append(list);
      }
    } catch (error) {
      result.textContent = error.name === 'TimeoutError' ? 'The answer took too long. Please try again.' :
        error instanceof TypeError ? 'The archive API could not be reached. Please start the Go server and try again.' : error.message;
    } finally { busy = false; submit.disabled = false; submit.textContent = 'Ask'; }
  });
  section.querySelectorAll('.ask-examples button').forEach(button => button.addEventListener('click', () => {
    if (busy) return;
    question.value = button.textContent; person.value = ''; form.requestSubmit();
  }));
})();
