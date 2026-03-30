/* ============================================================
   BurnoutGuard — Client-side JavaScript
   Chart.js rendering, API fetching, form handling
   ============================================================ */

(function () {
    "use strict";

    const STUDENT_ID = window.STUDENT_ID || "";

    // ── Mobile Menu Toggle ──────────────────────────────────
    const menuToggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");
    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
        // Close sidebar when a link is clicked (mobile)
        sidebar.querySelectorAll(".nav-links a").forEach((link) => {
            link.addEventListener("click", () => sidebar.classList.remove("open"));
        });
    }

    // ── Alert Banner Dismiss ────────────────────────────────
    const dismissBtn = document.getElementById("dismissAlert");
    const alertBanner = document.getElementById("alertBanner");
    if (dismissBtn && alertBanner) {
        dismissBtn.addEventListener("click", () => {
            alertBanner.classList.add("hidden");
        });
    }

    // ── Range Slider ↔ Number Input Sync ────────────────────
    const sliderPairs = [
        ["anxietySlider", "anxietyLevel"],
        ["sleepSlider", "sleepQuality"],
        ["studySlider", "studyLoad"],
        ["esteemSlider", "selfEsteem"],
        ["headacheSlider", "headache"],
    ];

    sliderPairs.forEach(([sliderId, inputId]) => {
        const slider = document.getElementById(sliderId);
        const input = document.getElementById(inputId);
        if (slider && input) {
            slider.addEventListener("input", () => (input.value = slider.value));
            input.addEventListener("input", () => (slider.value = input.value));
        }
    });

    // ── Session Form Submission ─────────────────────────────
    const sessionForm = document.getElementById("sessionForm");
    if (sessionForm) {
        sessionForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById("submitSession");
            submitBtn.disabled = true;
            submitBtn.textContent = "Submitting…";

            const payload = {
                student_id: document.getElementById("formStudentId").value,
                anxiety_level: parseInt(document.getElementById("anxietyLevel").value, 10),
                sleep_quality: parseInt(document.getElementById("sleepQuality").value, 10),
                study_load: parseInt(document.getElementById("studyLoad").value, 10),
                duration_min: parseFloat(document.getElementById("durationMin").value),
                typing_speed: parseFloat(document.getElementById("typingSpeed").value),
                break_count: parseInt(document.getElementById("breakCount").value, 10),
                self_esteem: parseInt(document.getElementById("selfEsteem").value, 10),
                headache: parseInt(document.getElementById("headache").value, 10),
                mental_health_history: 0,
                blood_pressure: 1,
                breathing_problem: 0,
            };

            try {
                const res = await fetch("/api/collect", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const data = await res.json();

                // Show result card
                const resultCard = document.getElementById("resultCard");
                const resultLabel = document.getElementById("resultLabel");
                const resultScore = document.getElementById("resultScore");

                if (resultCard && resultLabel && resultScore && data.prediction) {
                    resultLabel.textContent = data.prediction.label;
                    resultScore.textContent = `Confidence: ${(data.prediction.score * 100).toFixed(0)}%`;

                    resultCard.className = "result-card";
                    resultCard.classList.add(`result-${data.prediction.label.toLowerCase()}`);
                    resultCard.classList.remove("hidden");
                }
            } catch (err) {
                console.error("Submit error:", err);
                alert("Failed to submit session. Please try again.");
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = "Submit Session";
            }
        });
    }

    // ── Fetch and Render Prediction on Dashboard ────────────
    async function fetchPrediction() {
        if (!STUDENT_ID) return;
        try {
            const res = await fetch(`/api/predict/${STUDENT_ID}`);
            const data = await res.json();
            if (data.label) {
                updateRiskCard(data.label, data.score);
            }
        } catch (err) {
            console.error("Prediction fetch error:", err);
        }
    }

    function updateRiskCard(label, score) {
        const riskCard = document.getElementById("riskCard");
        const riskLabel = document.getElementById("riskLabel");
        const riskScore = document.getElementById("riskScore");

        if (riskCard) {
            riskCard.className = `risk-card risk-${label.toLowerCase()}`;
        }
        if (riskLabel) {
            riskLabel.textContent = label;
        }
        if (riskScore) {
            riskScore.innerHTML = `Confidence: <span class="mono">${(score * 100).toFixed(0)}%</span>`;
        }

        // Show/hide alert banner
        if (alertBanner) {
            if (label === "HIGH") {
                alertBanner.classList.remove("hidden");
            } else {
                alertBanner.classList.add("hidden");
            }
        }
    }

    // ── Fetch History and Render Chart ──────────────────────
    async function fetchHistory() {
        if (!STUDENT_ID) return;
        try {
            const res = await fetch(`/api/history/${STUDENT_ID}`);
            const data = await res.json();
            if (Array.isArray(data)) {
                renderHistoryChart(data);
                renderHistoryTable(data);
            }
        } catch (err) {
            console.error("History fetch error:", err);
        }
    }

    function renderHistoryChart(predictions) {
        const canvas = document.getElementById("riskChart") || document.getElementById("historyChart");
        if (!canvas || typeof Chart === "undefined") return;

        const labels = predictions.map((p) => {
            const d = new Date(p.predicted_at);
            return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
        });

        const scores = predictions.map((p) => p.risk_score);
        const colors = predictions.map((p) => {
            switch (p.risk_label) {
                case "HIGH": return "#A32D2D";
                case "MEDIUM": return "#BA7517";
                default: return "#1D9E75";
            }
        });

        new Chart(canvas, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Risk Score",
                        data: scores,
                        borderColor: "#6C3FEB",
                        backgroundColor: "rgba(108, 63, 235, 0.08)",
                        pointBackgroundColor: colors,
                        pointBorderColor: colors,
                        pointRadius: 6,
                        pointHoverRadius: 9,
                        borderWidth: 2.5,
                        tension: 0.35,
                        fill: true,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#2C2C2A",
                        titleFont: { family: "'Outfit'" },
                        bodyFont: { family: "'DM Mono'" },
                        callbacks: {
                            label: (ctx) => {
                                const p = predictions[ctx.dataIndex];
                                return `${p.risk_label}: ${(p.risk_score * 100).toFixed(0)}%`;
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        min: 0, max: 1,
                        ticks: { callback: (v) => `${(v * 100).toFixed(0)}%`, font: { family: "'DM Mono'" } },
                        grid: { color: "rgba(44,44,42,0.06)" },
                    },
                    x: {
                        ticks: { font: { family: "'Outfit'", size: 11 } },
                        grid: { display: false },
                    },
                },
            },
        });
    }

    function renderHistoryTable(predictions) {
        const tbody = document.getElementById("historyTableBody");
        if (!tbody) return;

        if (predictions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="empty-state">No predictions yet. Log a session to get started.</td></tr>';
            return;
        }

        tbody.innerHTML = predictions
            .slice()
            .reverse()
            .map((p) => {
                const d = new Date(p.predicted_at);
                const date = d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
                const pillClass = `risk-pill risk-pill-${p.risk_label.toLowerCase()}`;
                return `<tr>
                    <td>${date}</td>
                    <td><span class="${pillClass}">${p.risk_label}</span></td>
                    <td class="mono">${(p.risk_score * 100).toFixed(0)}%</td>
                </tr>`;
            })
            .join("");
    }

    // ── SHAP Explainability ─────────────────────────────────
    let shapChartInstance = null;
    let explanationFetched = false;

    window.toggleExplanation = async function () {
        const panel = document.getElementById("shapPanel");
        const wrap = document.querySelector(".shap-chart-wrap");
        const loader = document.getElementById("shapLoading");

        if (!panel) return;

        if (panel.classList.contains("hidden")) {
            panel.classList.remove("hidden");
            // Fetch if not already fetched
            if (!explanationFetched) {
                wrap.classList.add("hidden");
                loader.classList.remove("hidden");
                await fetchExplanation();
                loader.classList.add("hidden");
                wrap.classList.remove("hidden");
            }
        } else {
            panel.classList.add("hidden");
        }
    };

    async function fetchExplanation() {
        if (!STUDENT_ID) return;
        try {
            const res = await fetch(`/api/explain/${STUDENT_ID}`);
            const data = await res.json();

            if (data.error) {
                console.error("SHAP error:", data.error);
                return;
            }

            explanationFetched = true;
            renderShapChart(data);
        } catch (err) {
            console.error("Explanation fetch error:", err);
        }
    }

    function renderShapChart(data) {
        const canvas = document.getElementById("shapChart");
        if (!canvas || typeof Chart === "undefined") return;

        // data is sorted by absolute impact: [{"feature", "label", "value", "shap_value"}]
        // We only show top 5
        const top5 = data.slice(0, 5);

        // Chart.js horizontal bar charts put the first item at the bottom of the axis by default
        // So we reverse the arrays to keep highest impact at the top
        const labels = top5.map(d => `${d.label} [${d.value}]`).reverse();
        const shapValues = top5.map(d => d.shap_value).reverse();

        // Color coding: Positive SHAP (increases risk) = Red, Negative (decreases risk) = Teal
        const bgColors = shapValues.map(v => v > 0 ? "rgba(163, 45, 45, 0.85)" : "rgba(29, 158, 117, 0.85)");

        if (shapChartInstance) shapChartInstance.destroy();

        shapChartInstance = new Chart(canvas, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Contribution to Risk",
                    data: shapValues,
                    backgroundColor: bgColors,
                    borderRadius: 4,
                    barPercentage: 0.6,
                }],
            },
            options: {
                indexAxis: 'y', // Horizontal bar chart
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#2C2C2A",
                        titleFont: { family: "'Outfit'" },
                        bodyFont: { family: "'DM Mono'" },
                        callbacks: {
                            label: (ctx) => {
                                const val = ctx.raw;
                                const sign = val > 0 ? "+" : "";
                                return `Impact: ${sign}${val.toFixed(3)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: "rgba(44,44,42,0.06)" },
                        ticks: { font: { family: "'DM Mono'", size: 10 } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { family: "'Outfit'", size: 12, weight: 500 }, color: "#2C2C2A" }
                    }
                }
            }
        });
    }

    // ── Init ────────────────────────────────────────────────
    document.addEventListener("DOMContentLoaded", () => {
        // Dashboard page
        if (document.getElementById("riskCard")) {
            fetchPrediction();
            fetchHistory();
        }

        // History page
        if (document.getElementById("historyChart")) {
            fetchHistory();
        }
    });
})();

