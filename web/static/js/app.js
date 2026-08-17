/* ============================================================
   Just One More — Web 前端逻辑
   ============================================================ */

let currentTab = 1;

// ==================== 6个任务配置 ====================
const taskConfigs = {
  1: {
    title: '相似用户分析',
    desc: '基于用户-标签矩阵的余弦相似度计算，找出与目标用户兴趣最相似的用户群。',
    inputs: `<input type="text" class="input-field" id="mainInput" placeholder="请输入用户ID...">
             <button class="btn btn-primary" id="mainBtn" onclick="executeCurrentTask()">开始分析</button>`
  },
  2: {
    title: '视频推荐',
    desc: '基于协同过滤的个性化视频推荐，结合相似用户的观看偏好与内容特征。',
    inputs: `<input type="text" class="input-field" id="mainInput" placeholder="请输入用户ID...">
             <label class="enhanced-toggle"><input type="checkbox" id="enhancedCheck" onchange="toggleEnhancedMode()"> 算法增强</label>
             <button class="btn btn-primary" id="mainBtn" onclick="executeCurrentTask()">开始推荐</button>`
  },
  3: {
    title: '热度预测',
    desc: '使用 ARIMA 时间序列模型预测视频未来7天的累计观看量趋势。',
    inputs: `<input type="text" class="input-field" id="mainInput" placeholder="请输入视频ID...">
             <button class="btn btn-accent" id="mainBtn" onclick="executeCurrentTask()">开始预测</button>`
  },
  4: {
    title: '用户聚类分析',
    desc: '基于观看兴趣使用 MiniBatchKMeans + PCA 对用户进行聚类分组。',
    inputs: `<span class="input-label">聚类数量</span>
             <input type="number" class="input-field" id="mainInput" value="10" min="2" max="20" style="width:70px">
             <button class="btn btn-teal" id="mainBtn" onclick="executeCurrentTask()">开始聚类</button>`
  },
  5: {
    title: '视频聚类分析',
    desc: '基于用户交互模式使用 MiniBatchKMeans + TruncatedSVD 对视频进行聚类。',
    inputs: `<span class="input-label">聚类数量</span>
             <input type="number" class="input-field" id="mainInput" value="5" min="2" max="20" style="width:70px">
             <button class="btn btn-purple" id="mainBtn" onclick="executeCurrentTask()">开始聚类</button>`
  },
  6: {
    title: '推荐算法增强',
    desc: 'SVD 簇 Embedding / Thompson Sampling 冷启动 / LinUCB 动态优化 / 交互式反馈训练。',
    inputs: `<span class="input-label">Emb维度</span>
             <input type="number" class="input-field" id="mainInput" value="20" min="10" max="50" style="width:65px">
             <button class="btn btn-primary btn-sm" onclick="executeTask6('embedding')">① SVD</button>
             <button class="btn btn-warning btn-sm" onclick="executeTask6('thompson')">② TS训练</button>
             <button class="btn btn-accent btn-sm" onclick="executeTask6('linucb')">③ LinUCB训练</button>
             <button class="btn btn-teal btn-sm" onclick="startInteractiveTraining()">🎮 交互训练</button>
             <button class="btn btn-sm btn-reset" onclick="resetBandit()">↺ 重置</button>`
  }
};

// ==================== 初始化 ====================
console.log('[APP.JS v6] Script loaded at', new Date().toISOString());

// 显式挂载到 window 确保 onclick 能访问
window.executeCurrentTask = executeCurrentTask;
window.executeTask6 = executeTask6;

document.addEventListener('DOMContentLoaded', () => {
  console.log('[APP.JS v7] DOMContentLoaded fired');
  loadStats();
  triggerBurstAnimation();
  bindEvents();
  checkHealth();
  loadLeaderboard('views');
  console.log('[APP.JS v7] Init complete');
});

function bindEvents() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(Number(tab.dataset.tab)));
  });

  const crawlBtn = document.getElementById('btnCrawl');
  if (crawlBtn) crawlBtn.addEventListener('click', crawlRealData);

  // Enter 键提交
  document.getElementById('hcInputs').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') executeCurrentTask();
  });

  // 图片放大 Lightbox
  initLightbox();
}

// ==================== 实时统计 ====================
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    if (!data.success) return;

    animateNumber('statVideos', data.videos_count);
    animateNumber('statUsers', data.users_count);
    animateNumber('statOps', data.operations_count);

    setRing('statRingVideos', data.videos_count, 2000);
    setRing('statRingUsers', data.users_count, 20000);
    setRing('statRingOps', data.operations_count, Math.max(data.operations_count, 1));
  } catch (e) {}
}

function animateNumber(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const duration = 1500;
  const startTime = performance.now();
  function tick(now) {
    const p = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(target * eased).toLocaleString();
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function setRing(id, value, max) {
  const ring = document.getElementById(id);
  if (!ring) return;
  const circ = 107;
  setTimeout(() => { ring.style.strokeDashoffset = circ * (1 - Math.min(value / max, 1)); }, 300);
}

// ==================== 入场动画 ====================
function triggerBurstAnimation() {
  const icons = document.querySelectorAll('.platform-icon');
  const control = document.getElementById('heroControl');

  icons.forEach((icon, i) => {
    setTimeout(() => icon.classList.add('burst'), 150 + i * 70);
  });

  document.querySelectorAll('.crystal').forEach((el, i) => {
    setTimeout(() => { el.style.setProperty('--cd', (0.3 + i * 0.08) + 's'); el.classList.add('animate'); }, 400 + i * 80);
  });
  document.querySelectorAll('.sparkle').forEach((el, i) => {
    setTimeout(() => { el.style.setProperty('--sd', (0.5 + i * 0.1) + 's'); el.classList.add('animate'); }, 550 + i * 100);
  });

  setTimeout(() => {
    icons.forEach(icon => { icon.classList.remove('burst'); icon.classList.add('floating'); });
    if (control) control.classList.add('visible');
  }, 850);
}

// ==================== Tab 切换 ====================
function switchTab(tabId) {
  currentTab = tabId;

  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  const tabEl = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
  if (tabEl) tabEl.classList.add('active');

  updateHeroControl(tabId);

  document.querySelectorAll('.result-area').forEach(r => r.classList.remove('active'));
  const resultEl = document.getElementById('result' + tabId);
  if (resultEl) resultEl.classList.add('active');
}

function updateHeroControl(tabId) {
  const cfg = taskConfigs[tabId];
  if (!cfg) return;

  const control = document.getElementById('heroControl');
  control.style.opacity = '0';
  control.style.transform = 'translateY(8px)';

  setTimeout(() => {
    document.getElementById('hcTitle').textContent = cfg.title;
    document.getElementById('hcDesc').textContent = cfg.desc;
    document.getElementById('hcInputs').innerHTML = cfg.inputs;
    const input = document.getElementById('mainInput');
    if (input) setTimeout(() => input.focus(), 100);
    control.style.opacity = '1';
    control.style.transform = 'translateY(0)';
  }, 180);
}

// ==================== 执行入口 ====================
function executeCurrentTask() {
  const tid = currentTab;
  const resultEl = document.getElementById('result' + tid);
  const btn = document.getElementById('mainBtn');

  console.log('[DEBUG] executeCurrentTask called, tid=' + tid + ', resultEl=' + !!resultEl + ', btn=' + !!btn);

  if (btn) { btn.style.transform = 'scale(0.95)'; setTimeout(() => { if (btn) btn.style.transform = ''; }, 150); }

  // 确保结果区可见
  if (resultEl) {
    resultEl.classList.add('active');
    console.log('[DEBUG] result' + tid + ' classList added active');
  } else {
    console.error('[DEBUG] result' + tid + ' NOT FOUND!');
    showToast('结果区未找到，请刷新页面', 'error');
    return;
  }

  switch (tid) {
    case 1: callTask('similar-users', 1); break;
    case 2: callTask('recommend-videos', 2); break;
    case 3: callTask3(); break;
    case 4: callTask('user-clustering', 4); break;
    case 5: callTask('video-clustering', 5); break;
  }
}

// ==================== Task 1/2/4/5 ====================
async function callTask(endpoint, taskId) {
  const inputEl = document.getElementById('mainInput');
  const btn = document.getElementById('mainBtn');
  const resultEl = document.getElementById('result' + taskId);

  console.log('[DEBUG] callTask endpoint=' + endpoint + ' taskId=' + taskId + ' inputEl=' + !!inputEl + ' resultEl=' + !!resultEl);

  if (!inputEl || !resultEl) {
    showToast('页面元素未找到，请刷新', 'error');
    console.error('[DEBUG] Missing element: inputEl=' + !!inputEl + ' resultEl=' + !!resultEl);
    return;
  }

  let body = {};
  if (taskId === 1 || taskId === 2) {
    const val = inputEl.value.trim();
    if (!val) { showToast('请输入用户ID', 'error'); return; }
    if (!/^\d+$/.test(val)) { showToast('用户ID必须为数字', 'error'); return; }
    body.user_id = parseInt(val);
    if (taskId === 2) {
      body.use_enhanced = document.getElementById('enhancedCheck')?.checked || false;
    }
  } else if (taskId === 4 || taskId === 5) {
    body.n_clusters = parseInt(inputEl.value) || (taskId === 4 ? 10 : 5);
  }

  setLoading(true, btn, resultEl);
  showToast('正在执行分析...', 'success');

  try {
    const url = '/api/task' + taskId + '/' + endpoint;
    console.log('[DEBUG] Fetching ' + url + ' with body:', body);
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    console.log('[DEBUG] Response success=' + data.success + ' dataLen=' + (data.data ? data.data.length : 0));

    if (data.success) {
      const cfg = {
        1: { h: ['排名', '用户ID', '相似度'], k: ['rank', 'user_ID', 'similarity'] },
        2: { h: ['视频ID', '分类', '综合评分', data.enhanced_mode ? 'TS加成' : null, data.enhanced_mode ? 'LinUCB加成' : null, '推荐原因'].filter(Boolean),
             k: ['Video_ID', 'label', 'Overall_rating', data.enhanced_mode ? 'ts_boost' : null, data.enhanced_mode ? 'linucb_boost' : null, 'reason'].filter(Boolean) },
        4: { h: ['用户ID', '年龄', '聚类'], k: ['id', 'age', 'cluster'] },
        5: { h: ['视频ID', '分类', '观看数', '点赞数', '聚类'], k: ['id', 'tag', 'views', 'likes', 'cluster'] }
      }[taskId];

      // Task 2 特殊处理: 推荐原因可展开
      if (taskId === 2 && data.data) {
        data.data = data.data.map(row => ({
          ...row,
          reason: row.reason
            ? `<span class="reason-toggle" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none'">查看原因 ▸</span><div class="reason-text" style="display:none">${escapeHtml(row.reason)}</div>`
            : '—'
        }));
      }

      if (data.plot_url) {
        resultEl.innerHTML = `<div class="result-layout">
          <div class="result-table-wrap">${buildTable(cfg.h, data.data, cfg.k)}</div>
          <div class="result-chart-wrap"><img src="${data.plot_url}?t=${Date.now()}" alt="图表" onerror="this.parentElement.innerHTML=''"></div>
        </div>`;
      } else {
        resultEl.innerHTML = buildTable(cfg.h, data.data, cfg.k);
      }

      // 确保结果区可见并滚动
      resultEl.classList.add('active');
      console.log('[DEBUG] Result HTML set, scrolling to result' + taskId);

      // 先尝试 scrollIntoView
      setTimeout(() => {
        resultEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        console.log('[DEBUG] scrollIntoView called for result' + taskId);
      }, 100);

      // 备用方案：直接用 window.scrollTo
      setTimeout(() => {
        const rect = resultEl.getBoundingClientRect();
        const top = rect.top + window.pageYOffset - 80;
        window.scrollTo({ top: top, behavior: 'smooth' });
        console.log('[DEBUG] Fallback scrollTo y=' + top);
      }, 400);

      showToast('分析完成！滚动查看结果', 'success');
    } else {
      resultEl.innerHTML = `<div class="error-msg">${escapeHtml(data.error || '未知错误')}</div>`;
      showToast(data.error || '请求失败', 'error');
    }
  } catch (e) {
    console.error('[DEBUG] Fetch error:', e);
    resultEl.innerHTML = `<div class="error-msg">请求失败: ${escapeHtml(e.message)}</div>`;
    showToast('请求失败: ' + e.message, 'error');
  }
  setLoading(false, btn, null, taskId);
}

// ==================== Task 3 ====================
async function callTask3() {
  const inputEl = document.getElementById('mainInput');
  const btn = document.getElementById('mainBtn');
  const resultEl = document.getElementById('result3');

  if (!inputEl || !resultEl) { showToast('元素未找到', 'error'); return; }

  const val = inputEl.value.trim();
  if (!val) { showToast('请输入视频ID', 'error'); return; }
  if (!/^\d+$/.test(val)) { showToast('视频ID必须为数字', 'error'); return; }

  setLoading(true, btn, resultEl);
  showToast('正在预测...', 'success');

  try {
    console.log('[DEBUG] callTask3 fetching...');
    const res = await fetch('/api/task3/predict-heat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_id: parseInt(val) })
    });
    const data = await res.json();
    console.log('[DEBUG] Task3 response success=' + data.success);

    if (data.success) {
      const td = data.forecast.map((v, i) => ({ day: data.forecast_days[i], value: v }));
      resultEl.innerHTML = `<div class="result-layout">
        <div class="result-table-wrap">${buildTable(['预测天数', '预计观看量（累计）'], td, ['day', 'value'])}</div>
        <div class="result-chart-wrap"><img src="${data.plot_url}?t=${Date.now()}" alt="图表" onerror="this.parentElement.innerHTML=''"></div>
      </div>`;
      resultEl.classList.add('active');
      setTimeout(() => { resultEl.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 100);
      setTimeout(() => {
        const rect = resultEl.getBoundingClientRect();
        window.scrollTo({ top: rect.top + window.pageYOffset - 80, behavior: 'smooth' });
      }, 400);
      showToast('预测完成！滚动查看结果', 'success');
    } else {
      resultEl.innerHTML = `<div class="error-msg">${escapeHtml(data.error || '预测失败')}</div>`;
      showToast(data.error || '预测失败', 'error');
    }
  } catch (e) {
    console.error('[DEBUG] Task3 error:', e);
    resultEl.innerHTML = `<div class="error-msg">请求失败: ${escapeHtml(e.message)}</div>`;
    showToast('请求失败: ' + e.message, 'error');
  }
  setLoading(false, btn, null, 3);
}

// ==================== Task 6 ====================
function executeTask6(sub) {
  const endpoints = {
    embedding: { url: '/api/task6/embedding', body: true, btn: 0 },
    thompson:  { url: '/api/task6/thompson-sampling', body: true, btn: 1 },
    linucb:    { url: '/api/task6/linucb', body: true, btn: 2 }
  };
  const cfg = endpoints[sub];
  const resultEl = document.getElementById('result6');
  const inputEl = document.getElementById('mainInput');
  const dim = parseInt(inputEl?.value) || 20;

  if (!resultEl) return;
  resultEl.classList.add('active');

  // 禁用按钮
  const btns = document.querySelectorAll('#hcInputs button');
  btns.forEach(b => { b.disabled = true; if (b === btns[cfg.btn]) { b._t = b.textContent; b.textContent = '运行中...'; } });

  resultEl.innerHTML = '<div class="status-bar" style="color:#FB7299">状态：运行中...</div><div class="loading-spinner"><div class="spinner"></div>加载中...</div>';

  (async () => {
    try {
      const body = cfg.body ? { embedding_dim: dim, num_rounds: dim === 20 ? 30 : dim } : {};
      const res = await fetch(cfg.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();

      if (data.success) {
        let html = '';

        if (sub === 'embedding') {
          html = `<div class="status-bar" style="color:#52C41A">状态：SVD Embedding 生成完成</div>
            <table class="data-table"><thead><tr><th>模块</th><th>参数</th><th>结果</th><th>耗时</th></tr></thead><tbody>
              <tr><td>SVD Embedding</td><td>Dim=${dim}</td><td>U:${data.user_embeddings_shape} V:${data.video_embeddings_shape}</td><td>${data.runtime}</td></tr>
            </tbody></table>
            <p style="color:#aaa;margin-top:10px">Embedding 已保存，LinUCB 模型已重新加载</p>`;
        } else if (sub === 'thompson') {
          html = `<div class="status-bar" style="color:#52C41A">状态：Thompson Sampling 训练完成 (${data.rounds}轮)</div>`;
          html += `<div class="result-layout">
            <div class="result-table-wrap"><table class="data-table">
              <thead><tr><th>簇ID</th><th>Alpha</th><th>Beta</th><th>曝光N</th><th>估计CTR</th></tr></thead><tbody>`;
          const clusters = data.clusters || {};
          Object.keys(clusters).sort((a,b) => a-b).forEach(cid => {
            const c = clusters[cid];
            html += `<tr><td>簇${cid}</td><td>${c.alpha}</td><td>${c.beta}</td><td>${c.N}</td><td style="color:${c.ctr > 0.5 ? '#52C41A' : '#FF6B6B'}">${c.ctr}</td></tr>`;
          });
          html += `</tbody></table></div>
            <div class="result-chart-wrap"><img src="${data.ts_plot_url}?t=${Date.now()}" alt="TS分布" style="cursor:zoom-in"></div>
            ${data.ts_ctr_plot_url ? `<div class="result-chart-wrap"><img src="${data.ts_ctr_plot_url}?t=${Date.now()}" alt="CTR收敛" style="cursor:zoom-in"></div>` : ''}
          </div>`;
        } else if (sub === 'linucb') {
          html = `<div class="status-bar" style="color:#52C41A">状态：LinUCB 训练完成 (${data.rounds}轮)</div>`;
          const hist = data.linucb_history || [];
          if (hist.length > 0) {
            html += `<div class="result-layout"><div class="result-table-wrap"><table class="data-table">
              <thead><tr><th>轮次</th><th>臂 (U×V)</th><th>UCB分数</th><th>奖励</th></tr></thead><tbody>`;
            hist.forEach(h => {
              html += `<tr><td>${h.round}</td><td>${h.arm}</td><td>${h.ucb}</td><td>${h.reward}</td></tr>`;
            });
            html += `</tbody></table></div>
              ${data.linucb_plot_url ? `<div class="result-chart-wrap"><img src="${data.linucb_plot_url}?t=${Date.now()}" alt="LinUCB收敛" style="cursor:zoom-in"></div>` : ''}
            </div>`;
          }
        }

        resultEl.innerHTML = html;
      } else {
        resultEl.innerHTML = `<div class="status-bar" style="color:#FF6B6B">状态：失败 — ${escapeHtml(data.error)}</div>`;
        showToast(data.error, 'error');
      }
    } catch (e) {
      resultEl.innerHTML = `<div class="status-bar" style="color:#FF6B6B">状态：异常 — ${escapeHtml(e.message)}</div>`;
      showToast(e.message, 'error');
    }
    btns.forEach(b => { b.disabled = false; if (b._t) b.textContent = b._t; });
  })();
}

// ==================== 交互式训练 ====================
let interactiveRound = 0;

async function startInteractiveTraining() {
  const resultEl = document.getElementById('result6');
  if (!resultEl) return;
  resultEl.classList.add('active');
  resultEl.innerHTML = '<div class="loading-spinner"><div class="spinner"></div>准备候选视频...</div>';

  try {
    const res = await fetch('/api/task6/interactive-candidates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await res.json();
    if (!data.success) { showToast(data.error, 'error'); return; }

    interactiveRound = data.round;
    renderInteractiveUI(data);
  } catch (e) {
    resultEl.innerHTML = `<div class="error-msg">初始化失败: ${escapeHtml(e.message)}</div>`;
  }
}

function renderInteractiveUI(data) {
  const resultEl = document.getElementById('result6');
  if (!resultEl) return;

  let html = `<div class="interactive-panel">
    <div class="ip-header">
      <h3>🎮 交互式训练 — 第 ${interactiveRound} 轮</h3>
      <span class="ip-user">当前用户: #${data.user_id}</span>
      <span class="ip-status">${data.linucb_ready ? '🟢 LinUCB就绪' : '🟡 仅TS模式'}</span>
    </div>
    <div class="ip-candidates">`;

  data.candidates.forEach(c => {
    html += `<div class="ip-card">
      <div class="ip-card-header">
        <span class="ip-vid">视频 #${c.video_id}</span>
        <span class="ip-tag">${c.tag}</span>
      </div>
      <div class="ip-card-stats">
        <span>👁 ${c.views.toLocaleString()}</span>
        <span>👍 ${c.likes.toLocaleString()}</span>
      </div>
      <div class="ip-card-scores">
        <span class="ip-ts">TS 探索: ${c.ts_score}</span>
        <span class="ip-linucb">LinUCB: ${c.linucb_weight}</span>
      </div>
      <div class="ip-card-actions">
        <button class="ip-btn-like" onclick="submitFeedback(${data.user_id}, ${c.video_id}, true, this)">👍 喜欢</button>
        <button class="ip-btn-skip" onclick="submitFeedback(${data.user_id}, ${c.video_id}, false, this)">👎 跳过</button>
      </div>
    </div>`;
  });

  html += `</div>
    <div class="ip-plots" id="ipPlots"></div>
    <div class="ip-actions">
      <button class="btn btn-primary" onclick="startInteractiveTraining()">🔄 下一轮</button>
      <button class="btn btn-reset" onclick="resetBandit()">↺ 重置全部</button>
    </div>
  </div>`;

  resultEl.innerHTML = html;

  // 加载当前图表
  loadBanditPlots();
}

async function submitFeedback(userId, videoId, liked, btnEl) {
  // 只禁用当前卡片的按钮
  if (btnEl) {
    const card = btnEl.closest('.ip-card');
    if (card) {
      card.querySelectorAll('.ip-btn-like, .ip-btn-skip').forEach(b => { b.disabled = true; });
      // 标记整个卡片为已评分
      card.classList.add('rated');
      card.style.opacity = '0.7';
    }
    btnEl.textContent = liked ? '👍 已记录' : '👎 已记录';
    btnEl.style.background = liked ? '#52C41A' : '#FF6B6B';
    btnEl.style.color = '#fff';
  }

  try {
    const res = await fetch('/api/task6/interactive-feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, video_id: videoId, liked: liked })
    });
    const data = await res.json();
    if (!data.success) { showToast(data.error, 'error'); return; }

    // 更新图表
    loadBanditPlots();

    // 显示更新的簇状态
    const state = data.state;
    if (state && state.ts_clusters) {
      let clusterHtml = '<div class="ip-cluster-state"><h4>当前簇 CTR 估计</h4><div class="ip-cluster-grid">';
      Object.keys(state.ts_clusters).sort((a,b) => a-b).forEach(cid => {
        const c = state.ts_clusters[cid];
        if (c.N > 0) {
          clusterHtml += `<span class="ip-cluster-badge">簇${cid}: ${c.ctr} (N=${c.N})</span>`;
        }
      });
      clusterHtml += '</div></div>';
      const plotsEl = document.getElementById('ipPlots');
      if (plotsEl) plotsEl.insertAdjacentHTML('beforeend', clusterHtml);
    }

    showToast(`第${data.round}轮反馈已记录`, 'success');
  } catch (e) {
    showToast('反馈提交失败: ' + e.message, 'error');
  }
}

async function loadBanditPlots() {
  try {
    const res = await fetch('/api/task6/state');
    const data = await res.json();
    if (!data.success) return;

    const plotsEl = document.getElementById('ipPlots');
    if (!plotsEl) return;

    let plotHtml = '';
    if (data.ts_plot_url) plotHtml += `<div class="result-chart-wrap"><img src="${data.ts_plot_url}?t=${Date.now()}" alt="TS分布" style="cursor:zoom-in"></div>`;
    if (data.ts_ctr_plot_url) plotHtml += `<div class="result-chart-wrap"><img src="${data.ts_ctr_plot_url}?t=${Date.now()}" alt="CTR收敛" style="cursor:zoom-in"></div>`;
    if (data.linucb_plot_url) plotHtml += `<div class="result-chart-wrap"><img src="${data.linucb_plot_url}?t=${Date.now()}" alt="LinUCB" style="cursor:zoom-in"></div>`;

    // 替换图表区，保留 cluster state
    const clusterState = plotsEl.querySelector('.ip-cluster-state');
    plotsEl.innerHTML = plotHtml;
    if (clusterState) plotsEl.appendChild(clusterState);
  } catch (e) {}
}

async function resetBandit() {
  try {
    await fetch('/api/task6/reset', { method: 'POST' });
    interactiveRound = 0;
    const resultEl = document.getElementById('result6');
    if (resultEl) resultEl.innerHTML = '<div class="status-bar" style="color:#52C41A">状态：Bandit 已重置，可开始新的训练</div>';
    showToast('Bandit 状态已重置', 'success');
  } catch (e) {
    showToast('重置失败: ' + e.message, 'error');
  }
}

function toggleEnhancedMode() {
  const checked = document.getElementById('enhancedCheck')?.checked;
  showToast(checked ? '算法增强已开启 — 将应用 TS + LinUCB 动态权重' : '算法增强已关闭 — 使用标准协同过滤', 'success');
}

// ==================== 爬虫（带进度可视化） ====================
let crawlPollTimer = null;

async function crawlRealData() {
  const btn = document.getElementById('btnCrawl');
  const statusEl = document.getElementById('navStatus');
  if (!btn || btn.disabled) return;

  // 启动抓取
  btn.disabled = true; btn.textContent = '⏳ 启动中...';
  try {
    const res = await fetch('/api/crawl', { method: 'POST' });
    const data = await res.json();
    if (!data.success && data.error) {
      showToast(data.error, 'error');
      btn.disabled = false; btn.textContent = '📡 获取B站数据';
      return;
    }
  } catch (e) {
    btn.disabled = false; btn.textContent = '📡 获取B站数据';
    showToast('启动抓取失败: ' + e.message, 'error');
    return;
  }

  // 显示进度面板
  showCrawlOverlay();
  btn.textContent = '⏳ 抓取中...';

  // 轮询进度
  crawlPollTimer = setInterval(async () => {
    try {
      const r = await fetch('/api/crawl/progress');
      const p = await r.json();
      updateCrawlOverlay(p);
      if (!p.running) {
        clearInterval(crawlPollTimer);
        crawlPollTimer = null;
        setTimeout(() => hideCrawlOverlay(), 1500);
        if (p.error) {
          statusEl.textContent = '🔴 失败';
          showToast(p.error, 'error');
        } else {
          statusEl.textContent = '🟢 B站数据';
          showToast(`数据加载完成！视频:${p.videos_count} 用户:${p.users_count} 操作:${p.operations_count}`, 'success');
          loadStats();
        }
        btn.disabled = false; btn.textContent = '📡 获取B站数据';
      }
    } catch (e) {}
  }, 400);
}

function showCrawlOverlay() {
  let el = document.getElementById('crawlOverlay');
  if (!el) {
    el = document.createElement('div');
    el.id = 'crawlOverlay';
    el.className = 'crawl-overlay';
    el.innerHTML = `
      <div class="crawl-panel">
        <div class="crawl-glow"></div>
        <div class="crawl-header">
          <span class="crawl-title">📡 数据抓取中</span>
          <span class="crawl-phase" id="crawlPhase">初始化...</span>
        </div>
        <div class="crawl-track">
          <div class="crawl-bar" id="crawlBar"></div>
        </div>
        <div class="crawl-percent" id="crawlPercent">0%</div>
        <div class="crawl-detail" id="crawlDetail">准备开始...</div>
        <div class="crawl-stats">
          <div class="crawl-stat"><span class="cs-num" id="crawlVideos">0</span><span class="cs-label">视频</span></div>
          <div class="crawl-stat"><span class="cs-num" id="crawlUsers">0</span><span class="cs-label">用户</span></div>
          <div class="crawl-stat"><span class="cs-num" id="crawlOps">0</span><span class="cs-label">操作</span></div>
        </div>
        <div class="crawl-particles" id="crawlParticles"></div>
      </div>`;
    document.body.appendChild(el);

    // 粒子动画
    const container = el.querySelector('#crawlParticles');
    for (let i = 0; i < 12; i++) {
      const dot = document.createElement('span');
      dot.className = 'crawl-particle';
      dot.style.left = Math.random() * 100 + '%';
      dot.style.animationDelay = Math.random() * 2 + 's';
      dot.style.animationDuration = (1.5 + Math.random() * 2) + 's';
      container.appendChild(dot);
    }
  }
  el.classList.add('active');
}

function updateCrawlOverlay(p) {
  const bar = document.getElementById('crawlBar');
  const percent = document.getElementById('crawlPercent');
  const phase = document.getElementById('crawlPhase');
  const detail = document.getElementById('crawlDetail');

  if (bar) bar.style.width = p.percent + '%';
  if (percent) { percent.textContent = p.percent + '%'; percent.style.color = p.percent >= 95 ? '#52C41A' : '#FB7299'; }
  if (phase) phase.textContent = p.phase_text || '';
  if (detail) detail.textContent = p.detail || '';

  const v = document.getElementById('crawlVideos');
  const u = document.getElementById('crawlUsers');
  const o = document.getElementById('crawlOps');
  if (v) v.textContent = (p.videos_count || 0).toLocaleString();
  if (u) u.textContent = (p.users_count || 0).toLocaleString();
  if (o) o.textContent = (p.operations_count || 0).toLocaleString();
}

function hideCrawlOverlay() {
  const el = document.getElementById('crawlOverlay');
  if (el) el.classList.remove('active');
}

// ==================== 健康检查 ====================
async function checkHealth() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    const el = document.getElementById('navStatus');
    el.textContent = data.status === 'ok' ? '🟢 就绪' : '🔴 异常';
  } catch (e) {
    document.getElementById('navStatus').textContent = '🔴 离线';
  }
}

// ==================== 工具函数 ====================
function buildTable(headers, data, keys) {
  if (!data || data.length === 0) return '<div class="empty-state">暂无数据</div>';
  let h = '<table class="data-table"><thead><tr>';
  headers.forEach(x => { h += `<th>${x}</th>`; });
  h += '</tr></thead><tbody>';
  data.forEach(row => {
    h += '<tr>';
    keys.forEach(k => { h += `<td>${row[k] !== undefined ? row[k] : ''}</td>`; });
    h += '</tr>';
  });
  return h + '</tbody></table>';
}

function setLoading(loading, btn, resultEl, taskId) {
  if (loading) {
    if (btn) { btn.disabled = true; btn._t = btn.textContent; btn.textContent = '分析中...'; }
    if (resultEl) resultEl.innerHTML = '<div class="loading-spinner"><div class="spinner"></div>加载中...</div>';
  } else {
    if (btn) {
      btn.disabled = false;
      const d = {1:'开始分析',2:'开始推荐',3:'开始预测',4:'开始聚类',5:'开始聚类'};
      btn.textContent = btn._t || d[taskId] || '执行';
    }
  }
}

function showToast(msg, type) {
  const c = document.getElementById('toastContainer');
  if (!c) return;
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 5000);
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

// ==================== 图片放大 Lightbox ====================
function initLightbox() {
  const overlay = document.getElementById('lightboxOverlay');
  const img = document.getElementById('lightboxImg');
  const close = document.getElementById('lightboxClose');

  if (!overlay || !img || !close) return;

  // 事件委托：捕获所有结果区内的图片点击
  document.querySelector('.content-area').addEventListener('click', (e) => {
    if (e.target.tagName === 'IMG' && (e.target.closest('.result-chart-wrap') || e.target.closest('#ipPlots') || e.target.closest('#result6'))) {
      img.src = e.target.src;
      overlay.classList.add('active');
    }
  });

  // 关闭：点击 ❌
  close.addEventListener('click', () => overlay.classList.remove('active'));

  // 关闭：点击遮罩背景
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.classList.remove('active');
  });

  // 关闭：按 Escape 键
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('active')) {
      overlay.classList.remove('active');
    }
  });
}

// ==================== 热门排行榜 (MaxHeap Top-K) ====================
let leaderboardSort = 'views';

async function loadLeaderboard(sort) {
  const section = document.getElementById('leaderboardSection');
  const grid = document.getElementById('leaderboardGrid');
  if (!section || !grid) return;

  try {
    const res = await fetch('/api/top-videos?sort=' + sort);
    const data = await res.json();
    if (!data.success) return;

    section.style.display = 'block';
    grid.innerHTML = data.data.map((v, i) => {
      const rankClass = v.rank <= 3 ? ' rank-' + v.rank : '';
      return `<div class="lb-card${rankClass}">
        <span class="lb-card-rank">${v.rank}</span>
        <span class="lb-card-num">${v.rank}</span>
        <div class="lb-card-tag" title="视频 #${v.Video_ID}">#${v.Video_ID} ${v.tag}</div>
        <div class="lb-card-stats">
          观看 <span>${v.views.toLocaleString()}</span>
          点赞 <span>${v.likes.toLocaleString()}</span>
        </div>
      </div>`;
    }).join('');

    // 绑定排序按钮
    document.querySelectorAll('.lb-sort-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.sort === sort);
      btn.onclick = () => {
        leaderboardSort = btn.dataset.sort;
        loadLeaderboard(leaderboardSort);
      };
    });
  } catch (e) {}
}
