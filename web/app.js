const state = {
  mode: "local",
  filter: "all",
  result: null,
};

const elements = {
  form: document.querySelector("#scan-form"),
  input: document.querySelector("#target-input"),
  prefix: document.querySelector("#input-prefix"),
  button: document.querySelector("#scan-button"),
  repoName: document.querySelector("#repo-name"),
  grade: document.querySelector("#grade-chip"),
  scoreRing: document.querySelector("#score-ring"),
  scoreValue: document.querySelector("#score-value"),
  summary: document.querySelector("#score-summary"),
  passed: document.querySelector("#passed-count"),
  warnings: document.querySelector("#warning-count"),
  failed: document.querySelector("#failed-count"),
  scanTime: document.querySelector("#scan-time"),
  source: document.querySelector("#source-label"),
  categoryTotal: document.querySelector("#category-total"),
  categories: document.querySelector("#category-list"),
  recommendations: document.querySelector("#recommendation-list"),
  checks: document.querySelector("#check-list"),
  toast: document.querySelector("#toast"),
};

const statusLabels = { pass: "通过", warn: "建议", fail: "缺失" };

document.querySelectorAll(".mode-button").forEach((button) => {
  button.addEventListener("click", () => {
    state.mode = button.dataset.mode;
    document.querySelectorAll(".mode-button").forEach((item) => item.classList.toggle("active", item === button));
    if (state.mode === "local") {
      elements.prefix.textContent = "PATH";
      elements.input.value = ".";
      elements.input.placeholder = "输入本地仓库路径";
      elements.input.setAttribute("aria-label", "待扫描的本地路径");
    } else {
      elements.prefix.textContent = "URL";
      elements.input.value = "https://github.com/Seren927/learngit13";
      elements.input.placeholder = "https://github.com/owner/repo";
      elements.input.setAttribute("aria-label", "待扫描的 GitHub 仓库地址");
    }
  });
});

document.querySelectorAll(".filter-button").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll(".filter-button").forEach((item) => item.classList.toggle("active", item === button));
    renderChecks();
  });
});

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = elements.input.value.trim();
  if (state.mode === "local") {
    scan({ path: value || "." });
  } else {
    scan({ url: value });
  }
});

async function scan(payload) {
  setLoading(true);
  try {
    const response = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "扫描请求失败");
    state.result = data;
    render(data);
  } catch (error) {
    showToast(error.message);
  } finally {
    setLoading(false);
  }
}

function setLoading(loading) {
  elements.button.disabled = loading;
  elements.button.querySelector("span:first-child").textContent = loading ? "正在检测..." : "开始检测";
}

function render(result) {
  elements.repoName.textContent = result.repository;
  elements.grade.textContent = result.grade;
  elements.scoreValue.textContent = result.score;
  elements.scoreRing.style.setProperty("--score", result.score);
  elements.summary.textContent = result.summary;
  elements.passed.textContent = result.stats.passed;
  elements.warnings.textContent = result.stats.warnings;
  elements.failed.textContent = result.stats.failed;
  elements.categoryTotal.textContent = `${result.score} / 100`;
  elements.scanTime.textContent = new Date(result.generated_at).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
  elements.source.textContent = `${result.stats.mode} · ${result.stats.files} 个文件`;

  elements.categories.replaceChildren(
    ...result.categories.map((category) => {
      const row = document.createElement("div");
      row.className = `category-row${category.percent < 100 ? " warn" : ""}`;

      const name = document.createElement("span");
      name.className = "category-name";
      name.textContent = category.label;

      const track = document.createElement("div");
      track.className = "category-track";
      const bar = document.createElement("div");
      bar.className = "category-bar";
      bar.style.width = `${category.percent}%`;
      track.append(bar);

      const score = document.createElement("span");
      score.className = "category-score";
      score.textContent = `${category.points}/${category.max_points}`;

      row.append(name, track, score);
      return row;
    }),
  );

  elements.recommendations.replaceChildren(
    ...result.recommendations.map((text) => {
      const item = document.createElement("li");
      item.textContent = text;
      return item;
    }),
  );

  renderChecks();
}

function renderChecks() {
  if (!state.result) return;
  const checks = state.result.checks.filter(
    (check) => state.filter === "all" || check.status !== "pass",
  );
  if (!checks.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "没有待改进项目，当前检查全部通过。";
    elements.checks.replaceChildren(empty);
    return;
  }

  elements.checks.replaceChildren(
    ...checks.map((check) => {
      const row = document.createElement("div");
      row.className = "check-row";
      row.setAttribute("role", "row");

      const status = document.createElement("span");
      status.className = `status-tag ${check.status}`;
      status.textContent = statusLabels[check.status];

      const title = document.createElement("div");
      title.className = "check-title";
      title.textContent = check.title;
      const description = document.createElement("small");
      description.textContent = check.description;
      title.append(description);

      const evidence = document.createElement("span");
      evidence.className = "check-evidence";
      evidence.textContent = check.evidence;

      const points = document.createElement("span");
      points.className = "check-points";
      points.textContent = `${check.points}/${check.max_points}`;

      row.append(status, title, evidence, points);
      return row;
    }),
  );
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => elements.toast.classList.remove("show"), 4200);
}

window.addEventListener("DOMContentLoaded", () => scan({ path: "." }));

