// ── Máscara CPF ───────────────────────────────────────────────────
const cpfInput = document.getElementById('cpf');
if (cpfInput) {
  cpfInput.addEventListener('input', function () {
    let v = this.value.replace(/\D/g, '').slice(0, 11);
    if (v.length > 9)      this.value = v.slice(0,3)+'.'+v.slice(3,6)+'.'+v.slice(6,9)+'-'+v.slice(9);
    else if (v.length > 6) this.value = v.slice(0,3)+'.'+v.slice(3,6)+'.'+v.slice(6);
    else if (v.length > 3) this.value = v.slice(0,3)+'.'+v.slice(3);
    else                   this.value = v;
  });
}

// ── Máscara Telefone ──────────────────────────────────────────────
const telInput = document.getElementById('telefone');
if (telInput) {
  telInput.addEventListener('input', function () {
    let v = this.value.replace(/\D/g, '').slice(0, 11);
    if (v.length > 6)      this.value = '('+v.slice(0,2)+') '+v.slice(2,7)+'-'+v.slice(7);
    else if (v.length > 2) this.value = '('+v.slice(0,2)+') '+v.slice(2);
    else if (v.length > 0) this.value = '('+v;
    else                   this.value = '';
  });
}

// ── Slider nível de dor ───────────────────────────────────────────
const dorSlider = document.getElementById('nivel_dor');
const dorValue  = document.getElementById('dor_value');
if (dorSlider && dorValue) {
  dorSlider.addEventListener('input', function () {
    dorValue.textContent = this.value;
    const cores = ['#48bb78','#48bb78','#48bb78','#f6e05e','#f6e05e',
                   '#f6e05e','#ed8936','#ed8936','#fc4444','#fc4444','#fc4444'];
    dorValue.style.color = cores[parseInt(this.value)];
  });
}

// ── Abas de regiões de sintomas ───────────────────────────────────
const tabs   = document.querySelectorAll('.region-tab');
const grids  = document.querySelectorAll('.sintomas-grid');

tabs.forEach(tab => {
  tab.addEventListener('click', function () {
    tabs.forEach(t => t.classList.remove('active'));
    grids.forEach(g => g.classList.remove('visible'));
    this.classList.add('active');
    const region = this.dataset.region;
    const grid   = document.getElementById('grid-' + region);
    if (grid) grid.classList.add('visible');
  });
});

// Abre primeira aba por padrão
if (tabs.length > 0) tabs[0].click();

// ── Checkbox sintomas com highlight ──────────────────────────────
document.querySelectorAll('.sintoma-item').forEach(item => {
  const cb = item.querySelector('input[type=checkbox]');
  item.addEventListener('click', function (e) {
    if (e.target !== cb) cb.checked = !cb.checked;
    item.classList.toggle('checked', cb.checked);
  });
  if (cb.checked) item.classList.add('checked');
});

// ── Anima barras de progresso no resultado ────────────────────────
document.querySelectorAll('.proba-bar-fill').forEach(bar => {
  const pct = bar.dataset.pct;
  bar.style.width = '0%';
  setTimeout(() => { bar.style.width = pct + '%'; }, 200);
});