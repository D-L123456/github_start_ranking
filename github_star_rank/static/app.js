(function () {
    const LANG_COLORS = {
        "Python": "python", "JavaScript": "javascript", "TypeScript": "typescript",
        "Java": "java", "Go": "go", "Rust": "rust", "C++": "c++",
        "C": "c", "C#": "c#", "Ruby": "ruby", "PHP": "php",
        "Swift": "swift", "Kotlin": "kotlin", "Scala": "scala",
        "Shell": "shell", "Dart": "dart", "HTML": "html", "CSS": "css",
    };

    let currentSince = "daily";
    let currentLang = "";
    let currentSearch = "";
    let allRepos = [];
    let refreshTimer = null;

    const repoListEl = document.getElementById("repo-list");
    const loadingEl = document.getElementById("loading");
    const errorEl = document.getElementById("error");
    const updateTimeEl = document.getElementById("update-time");
    const btnRefresh = document.getElementById("btn-refresh");
    const sinceGroup = document.getElementById("since-group");
    const langSelect = document.getElementById("lang-select");
    const searchInput = document.getElementById("search-input");

    function formatNumber(n) {
        if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, "") + "k";
        return n.toString();
    }

    function formatTime(isoStr) {
        if (!isoStr) return "";
        const d = new Date(isoStr);
        return d.toLocaleString("zh-CN", {
            month: "2-digit", day: "2-digit",
            hour: "2-digit", minute: "2-digit",
        });
    }

    function getLangColorClass(lang) {
        const key = LANG_COLORS[lang];
        return key ? `lang-color-${key}` : "lang-color-default";
    }

    function renderRepos(repos) {
        if (repos.length === 0) {
            repoListEl.innerHTML = '<div class="loading"><p>暂无数据</p></div>';
            return;
        }

        repoListEl.innerHTML = repos.map((repo) => {
            const rankClass = repo.rank === 1 ? "top1" : repo.rank === 2 ? "top2" : repo.rank === 3 ? "top3" : "";
            const langDot = repo.language
                ? `<span class="lang-dot ${getLangColorClass(repo.language)}"></span>`
                : "";

            return `
            <div class="repo-card">
                <div class="repo-rank ${rankClass}">${repo.rank}</div>
                <div class="repo-info">
                    <div class="repo-name">
                        <a href="${repo.url}" target="_blank" rel="noopener">
                            <span class="owner">${repo.owner}/</span>${repo.name}
                        </a>
                    </div>
                    <div class="repo-desc" title="${repo.description || ''}">${repo.description || "暂无描述"}</div>
                    <div class="repo-meta">
                        ${repo.language ? `<span class="lang">${langDot} ${repo.language}</span>` : ""}
                        <span class="stars">★ ${formatNumber(repo.total_stars)}</span>
                        <span class="stars">⑂ ${formatNumber(repo.total_forks)}</span>
                    </div>
                </div>
                <div class="repo-stats">
                    <span class="stars-today">+${formatNumber(repo.stars_since)}</span>
                    <span class="stars-today-label">${repo.since_label}</span>
                    <span class="stars-total">总 ★ ${formatNumber(repo.total_stars)}</span>
                </div>
            </div>`;
        }).join("");
    }

    function applyFilters() {
        let filtered = allRepos;

        if (currentLang) {
            filtered = filtered.filter((r) => r.language && r.language.toLowerCase() === currentLang.toLowerCase());
        }

        if (currentSearch) {
            const q = currentSearch.toLowerCase();
            filtered = filtered.filter(
                (r) =>
                    r.full_name.toLowerCase().includes(q) ||
                    (r.description && r.description.toLowerCase().includes(q))
            );
        }

        filtered = filtered.map((r, i) => ({ ...r, rank: i + 1 }));
        renderRepos(filtered);
    }

    async function fetchTrending(since, force = false) {
        loadingEl.style.display = "block";
        errorEl.style.display = "none";
        repoListEl.innerHTML = "";

        try {
            const params = new URLSearchParams({ since });
            if (force) params.set("force", "1");

            const resp = await fetch(`/api/trending?${params}`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

            const data = await resp.json();
            allRepos = data.repos || [];

            if (data.updated_at) {
                updateTimeEl.textContent = `更新于 ${formatTime(data.updated_at)}`;
            }

            applyFilters();
        } catch (err) {
            console.error("Failed to fetch trending:", err);
            errorEl.style.display = "block";
        } finally {
            loadingEl.style.display = "none";
        }
    }

    async function forceRefresh() {
        btnRefresh.disabled = true;
        btnRefresh.classList.add("spinning");

        try {
            await fetch(`/api/refresh?since=${currentSince}`, { method: "POST" });
            await fetchTrending(currentSince);
        } finally {
            btnRefresh.disabled = false;
            btnRefresh.classList.remove("spinning");
        }
    }

    sinceGroup.addEventListener("click", (e) => {
        const btn = e.target.closest(".btn-filter");
        if (!btn) return;

        sinceGroup.querySelectorAll(".btn-filter").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        currentSince = btn.dataset.since;
        fetchTrending(currentSince);
    });

    langSelect.addEventListener("change", () => {
        currentLang = langSelect.value;
        applyFilters();
    });

    let searchDebounce = null;
    searchInput.addEventListener("input", () => {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(() => {
            currentSearch = searchInput.value.trim();
            applyFilters();
        }, 300);
    });

    btnRefresh.addEventListener("click", forceRefresh);

    async function loadLanguages() {
        try {
            const resp = await fetch("/api/languages");
            const data = await resp.json();
            const languages = data.languages || {};
            const keys = Object.keys(languages).sort();
            keys.forEach((k) => {
                const opt = document.createElement("option");
                opt.value = languages[k];
                opt.textContent = languages[k];
                langSelect.appendChild(opt);
            });
        } catch (err) {
            console.error("Failed to load languages:", err);
        }
    }

    function startAutoRefresh() {
        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(() => {
            fetchTrending(currentSince);
        }, 30 * 60 * 1000);
    }

    async function init() {
        await loadLanguages();
        await fetchTrending(currentSince);
        startAutoRefresh();
    }

    init();
})();