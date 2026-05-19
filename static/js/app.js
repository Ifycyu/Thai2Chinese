let analysisData = null;
let activeWordIndex = -1;
let currentAudio = null;
let currentController = null;
let isProcessing = false;

const TONE_CLASS = {
    mid: "tone-mid",
    low: "tone-low",
    falling: "tone-falling",
    high: "tone-high",
    rising: "tone-rising",
};

const TONE_CN = {
    mid: "中声调", low: "低声调", falling: "降声调",
    high: "高声调", rising: "升声调",
};

const TONE_NUM_CN = {
    1: "第1调", 2: "第2调", 3: "第3调", 4: "第4调", 5: "第5调",
};

const TONE_MARK_NUM = {
    "่": "第2声调",
    "้": "第3声调",
    "๊": "第4声调",
    "๋": "第5声调",
};

function getHeaders() {
    return {
        "X-Dict-API": localStorage.getItem("DICT_API_URL") || "",
        "X-Translate-Endpoint": localStorage.getItem("TRANSLATE_API_ENDPOINT") || "",
        "X-Translate-Token": localStorage.getItem("TRANSLATE_AUTH_TOKEN") || "",
        "X-Translate-Model": localStorage.getItem("TRANSLATE_MODEL") || "",
    };
}

async function analyzeSentence() {
    const input = document.getElementById("thaiInput");
    const sentence = input.value.trim();
    if (!sentence || isProcessing) return;

    const analyzeBtn = document.getElementById("analyzeBtn");
    const cancelBtn = document.getElementById("cancelBtn");
    const loadingBar = document.getElementById("loadingBar");
    const statusText = document.getElementById("statusText");
    const results = document.getElementById("results");
    const detailPanel = document.getElementById("detailPanel");

    isProcessing = true;
    analyzeBtn.disabled = true;
    cancelBtn.style.display = "inline-block";
    loadingBar.classList.add("show");
    statusText.classList.add("show");
    statusText.textContent = "分析中，你可以继续编辑...";
    results.classList.add("hidden");
    detailPanel.classList.add("hidden");
    activeWordIndex = -1;

    currentController = new AbortController();

    try {
        const resp = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getHeaders(),
            },
            body: JSON.stringify({ sentence }),
            signal: currentController.signal
        });
        if (!resp.ok) throw new Error("分析失败");
        analysisData = await resp.json();
        renderSentence(analysisData);
        results.classList.remove("hidden");
    } catch (err) {
        if (err.name !== "AbortError") {
            alert("分析出错：" + err.message);
        }
    } finally {
        isProcessing = false;
        analyzeBtn.disabled = false;
        cancelBtn.style.display = "none";
        loadingBar.classList.remove("show");
        statusText.classList.remove("show");
        currentController = null;
    }
}

function cancelAnalyze() {
    if (currentController) {
        currentController.abort();
    }
}

function renderSentence(data) {
    const container = document.getElementById("sentenceDisplay");
    container.innerHTML = "";

    data.words.forEach((word, idx) => {
        const span = document.createElement("span");
        span.className = "word-span";
        span.dataset.index = idx;

        const wordText = document.createElement("span");
        wordText.className = "word-text";
        wordText.textContent = word.word;

        const classBadge = document.createElement("span");
        classBadge.className = "word-class-badge";
        classBadge.textContent = word.chinese_def;

        const speakerBtn = document.createElement("button");
        speakerBtn.className = "speaker-btn";
        speakerBtn.textContent = "\u{1F50A}";
        speakerBtn.title = "点击发音";
        speakerBtn.onclick = (e) => {
            e.stopPropagation();
            playWord(word.word);
        };

        span.appendChild(wordText);
        span.appendChild(classBadge);
        span.appendChild(speakerBtn);

        span.addEventListener("mouseenter", (e) => showTooltip(e, word));
        span.addEventListener("mouseleave", hideTooltip);
        span.addEventListener("click", () => showDetail(idx));

        container.appendChild(span);
        if (idx < data.words.length - 1) {
            const space = document.createElement("span");
            space.className = "word-space";
            container.appendChild(space);
        }
    });
}

function showTooltip(event, word) {
    const tooltip = document.getElementById("tooltip");
    tooltip.innerHTML = buildTooltipHTML(word);
    tooltip.classList.remove("hidden");
    positionTooltip(event, tooltip);
}

function hideTooltip() {
    document.getElementById("tooltip").classList.add("hidden");
}

function positionTooltip(event, tooltip) {
    const rect = event.target.getBoundingClientRect();
    let top = rect.bottom + 10;
    let left = rect.left;

    tooltip.style.visibility = "hidden";
    tooltip.classList.remove("hidden");
    const tipW = tooltip.offsetWidth;
    const tipH = tooltip.offsetHeight;

    if (left + tipW > window.innerWidth - 10) left = window.innerWidth - tipW - 10;
    if (left < 10) left = 10;
    if (top + tipH > window.innerHeight - 10) top = rect.top - tipH - 10;
    if (top < 10) top = 10;

    tooltip.style.top = top + "px";
    tooltip.style.left = left + "px";
    tooltip.style.visibility = "visible";
}

function buildTooltipHTML(w) {
    let h = "";
    h += `<div class="tip-word">${w.word}</div>`;
    h += `<div class="tip-phonetic">${w.phonetic || w.ipa || ""}</div>`;
    const abbr = w.word_class_abbr ? `（${w.word_class_abbr}）` : "";
    h += `<div class="tip-meta">词性：${w.word_class}${abbr}</div>`;
    h += `<div class="tip-definition">${w.chinese_def}</div>`;

    if (w.syllables && w.syllables.length > 0) {
        const toneInfo = w.syllables.map(syl => {
            const toneNum = TONE_NUM_CN[syl.tone_number] || "";
            return `${syl.text} → ${toneNum}`;
        }).join("  ");
        h += `<div class="tip-tone-summary">${toneInfo}</div>`;
    }

    return h;
}

function classCN(cls) {
    return { mid: "中辅音", high: "高辅音", low: "低辅音" }[cls] || cls;
}

function showDetail(idx) {
    if (!analysisData || !analysisData.words[idx]) return;
    document.querySelectorAll(".word-span").forEach(el => {
        el.classList.toggle("active", parseInt(el.dataset.index) === idx);
    });
    activeWordIndex = idx;

    const w = analysisData.words[idx];
    const panel = document.getElementById("detailPanel");

    let h = `<div class="dp-header">`;
    h += `<div class="dp-word">${w.word}</div>`;
    h += `<button class="dp-speaker" onclick="playWord('${w.word}')" title="点击发音">\u{1F50A}</button>`;
    h += `<div class="dp-info">`;
    h += `<div class="dp-ipa">${w.phonetic || w.ipa || ""}</div>`;
    h += `<div class="dp-meta">词类：${w.word_class}${w.word_class_abbr ? "（" + w.word_class_abbr + "）" : ""}</div>`;
    h += `</div></div>`;

    h += `<div class="dp-def">${w.chinese_def}</div>`;
    h += `<div class="dp-dict-raw"><button class="dp-dict-btn" onclick="lookupDictRaw('${w.word}')">📖 查词典</button><div id="dictRawResult"></div></div>`;

    if (w.syllables && w.syllables.length > 0) {
        h += `<h4 style="margin:1rem 0 0.5rem;color:#667eea;">声调分析</h4>`;
        w.syllables.forEach(syl => {
            const tc = TONE_CLASS[syl.tone] || "";
            const toneNum = TONE_NUM_CN[syl.tone_number] || "";

            h += `<div class="tone-explanation">`;
            h += `<div class="syl-label">${syl.text} <span class="${tc}" style="padding:0.1rem 0.4rem;border-radius:4px;font-size:0.85rem;">${syl.tone_cn || TONE_CN[syl.tone]} ${toneNum}</span></div>`;
            if (syl.ipa) h += `<span class="syl-ipa-label">[${syl.ipa}]</span>`;
            h += `<div class="explanation-text">${syl.tone_explanation}</div>`;
            if (syl.pronunciation_tip) h += `<div style="margin-top:0.3rem;color:#667eea;font-size:0.85rem;">发音提示：${syl.pronunciation_tip}</div>`;
            h += `</div>`;
        });
    }

    if (w.examples && w.examples.length > 0) {
        h += `<div class="dp-section"><h4>例句</h4>`;
        w.examples.forEach((ex, i) => {
            h += `<div class="dp-example">`;
            h += `<span class="ex-thai">${i + 1}. ${ex.thai}</span><br>`;
            h += `<span class="ex-chinese">→ ${ex.chinese}</span>`;
            h += `</div>`;
        });
        h += `</div>`;
    }

    if (w.compounds && w.compounds.length > 0) {
        h += `<div class="dp-section"><h4>常用搭配</h4>`;
        w.compounds.forEach(c => { h += `<span class="dp-compound">${c}</span>`; });
        h += `</div>`;
    }

    panel.innerHTML = h;
    panel.classList.remove("hidden");
    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function playWord(word) {
    if (currentAudio) { currentAudio.pause(); currentAudio = null; }
    try {
        currentAudio = new Audio(`/api/tts/${encodeURIComponent(word)}`);
        currentAudio.play();
    } catch {
        if ("speechSynthesis" in window) {
            const u = new SpeechSynthesisUtterance(word);
            u.lang = "th-TH";
            speechSynthesis.speak(u);
        }
    }
}

async function lookupDictRaw(word) {
    const resultDiv = document.getElementById("dictRawResult");
    if (!resultDiv) return;

    const dictApi = localStorage.getItem("DICT_API_URL") || "";
    if (!dictApi) {
        resultDiv.innerHTML = `<div class="dict-raw-content dict-raw-error">请先在设置中配置词典API地址</div>`;
        return;
    }

    resultDiv.innerHTML = `<div class="dict-raw-content">查询中...</div>`;

    try {
        const resp = await fetch(`/api/dict-raw/${encodeURIComponent(word)}`, {
            headers: { "X-Dict-API": dictApi }
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }
        const data = await resp.json();

        // Parse and display nicely
        let h = `<div class="dict-raw-content">`;
        const items = data["1"]?.list || [];
        if (items.length === 0) {
            h += `<div class="dict-raw-empty">词典无结果</div>`;
        } else {
            items.forEach(item => {
                h += `<div class="dict-raw-item">`;
                if (item.word) h += `<div class="dict-raw-word">${item.word}</div>`;
                if (item.explain) h += `<div class="dict-raw-explain">${item.explain}</div>`;
                if (item.pronu) h += `<div class="dict-raw-pronu">发音：${item.pronu}</div>`;
                if (item.thesaurus && item.thesaurus !== "[]") h += `<div class="dict-raw-syn">近义：${item.thesaurus}</div>`;
                if (item.fyfx) h += `<div class="dict-raw-fyfx">${item.fyfx.replace(/\r\n/g, "<br>").replace(/\r/g, "<br>")}</div>`;
                if (item.mp3) h += `<div class="dict-raw-mp3">🔊 <a href="https://xcxapi.seak.online/wxapi/t1/t2cv2?tp=3&id=${item.mp3}" target="_blank">${item.mp3}</a></div>`;
                h += `</div>`;
            });
        }
        h += `</div>`;
        resultDiv.innerHTML = h;
    } catch (e) {
        resultDiv.innerHTML = `<div class="dict-raw-content dict-raw-error">查询失败：${e.message}</div>`;
    }
}

document.getElementById("thaiInput").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        analyzeSentence();
    }
});
