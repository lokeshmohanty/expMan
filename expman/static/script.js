/**
 * ExpMan Frontend Logic
 */

const App = {
    state: {
        experiments: [],
        currentExperiment: null,
        selectedRuns: new Set(),
        runsData: {}, // Cache: run_id -> { metrics: [], config: {} }
        configs: {},
        activeTab: 'metrics'
    },

    init: async () => {
        // Setup Tab Navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => App.setTab(e.target.dataset.tab));
        });

        // Load Experiments
        await App.fetchExperiments();

        // Setup auto-refresh
        setInterval(App.refreshData, 10000);

        // Setup Plot Resize
        const slider = document.getElementById('plot-size-slider');
        if (slider) {
            slider.addEventListener('input', (e) => App.updatePlotSize(e.target.value));
        }
    },

    updatePlotSize: (size) => {
        const container = document.getElementById('charts-container');
        const label = document.getElementById('plot-size-label');
        const ratio = 1.0; // Maintain 1:1 (Square) aspect ratio
        const height = Math.round(size * ratio);

        if (container) {
            container.style.gridTemplateColumns = `repeat(auto-fill, minmax(${size}px, 1fr))`;

            // Update height of all plot cards
            const cards = container.querySelectorAll('.card');
            cards.forEach(card => {
                card.style.minHeight = `${height}px`;
                card.style.height = `${height}px`; // Force height for ratio
            });
        }
        if (label) {
            label.innerText = `${size}px`;
        }

        // Force Reflow for Plotly
        const param = { autosize: true };
        const plots = container.querySelectorAll('.js-plotly-plot');
        plots.forEach(div => Plotly.relayout(div, param));
    },

    setTab: (tabName) => {
        App.state.activeTab = tabName;

        // Update Buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active', 'text-brand-600', 'border-b-2', 'border-brand-600');
                btn.classList.remove('text-gray-500', 'border-transparent');
            } else {
                btn.classList.remove('active', 'text-brand-600', 'border-b-2', 'border-brand-600');
                btn.classList.add('text-gray-500');
            }
        });

        // Update Content
        document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
        document.getElementById(`tab-${tabName}`).classList.remove('hidden');

        // Trigger specific renders
        // For artifacts, we now support multiple.
        const lastRun = Array.from(App.state.selectedRuns).pop();
        if (tabName === 'artifacts') App.renderArtifactsTab();
    },

    fetchExperiments: async () => {
        try {
            const res = await fetch('/api/experiments');
            const exps = await res.json();
            App.state.experiments = exps;

            const select = document.getElementById('experiment-select');
            select.innerHTML = '<option disabled selected>Select Experiment</option>' +
                exps.map(e => `<option value="${e}">${e}</option>`).join('');

            select.addEventListener('change', (e) => App.selectExperiment(e.target.value));
        } catch (e) {
            console.error("Failed to fetch experiments", e);
        }
    },

    refreshData: async () => {
        if (!App.state.currentExperiment) return;

        // Poll for new runs structure
        await App.fetchRunsList(App.state.currentExperiment);

        // Reload data for selected runs
        for (let runId of App.state.selectedRuns) {
            await App.loadRunData(runId);
        }
        App.renderDashboard();

        const status = document.getElementById('refresh-indicator');
        if (status) status.innerText = new Date().toLocaleTimeString();
    },

    selectExperiment: async (name) => {
        App.state.currentExperiment = name;
        App.state.selectedRuns.clear();
        App.state.runsData = {};
        await App.fetchRunsList(name);
    },

    fetchRunsList: async (name) => {
        try {
            const res = await fetch(`/api/experiments/${name}/runs`);
            const runs = await res.json();

            // Check if list changed to avoid unnecessary DOM thrashing (optional but good)
            // For now, naive re-render is fine if we preserve selection state visually

            const container = document.getElementById('runs-container');
            container.innerHTML = runs.map(run => {
                const isSelected = App.state.selectedRuns.has(run);
                const activeClass = isSelected ? 'active' : '';
                const checkBg = isSelected ? 'bg-brand-600 border-brand-600' : 'bg-transparent border-gray-600';
                const iconOpacity = isSelected ? '' : 'opacity-0';

                return `
                <div class="run-item group flex items-center justify-between p-2 rounded-md cursor-pointer transition-all border border-transparent ${activeClass}"
                     onclick="App.toggleRun('${run}', this)">
                    <div class="flex items-center gap-2">
                        <div class="w-4 h-4 rounded border flex items-center justify-center checkbox transition-colors ${checkBg}" id="check-${run}">
                            <i class="ri-check-line text-white text-xs ${iconOpacity}"></i>
                        </div>
                        <span class="text-sm font-medium label-text">${run}</span>
                    </div>
                    <i class="ri-arrow-right-s-line text-gray-500 opacity-0 group-hover:opacity-100"></i>
                </div>
            `}).join('');
        } catch (e) {
            console.error("Failed to fetch runs", e);
        }
    },

    toggleRun: async (runId, el) => {
        const checkbox = el.querySelector('.checkbox');
        const icon = checkbox.querySelector('i');

        if (App.state.selectedRuns.has(runId)) {
            App.state.selectedRuns.delete(runId);
            checkbox.classList.remove('bg-brand-600', 'border-brand-600');
            checkbox.classList.add('bg-transparent', 'border-gray-600');
            icon.classList.add('opacity-0');
            el.classList.remove('active');
        } else {
            App.state.selectedRuns.add(runId);
            checkbox.classList.remove('bg-transparent', 'border-gray-600');
            checkbox.classList.add('bg-brand-600', 'border-brand-600');
            icon.classList.remove('opacity-0');
            el.classList.add('active');

            if (!App.state.runsData[runId]) {
                await App.loadRunData(runId);
            }
        }

        App.renderDashboard();
    },

    loadRunData: async (runId) => {
        const exp = App.state.currentExperiment;
        const [metrics, config] = await Promise.all([
            fetch(`/api/experiments/${exp}/runs/${runId}/metrics`).then(r => r.json()),
            fetch(`/api/experiments/${exp}/runs/${runId}/config`).then(r => r.json())
        ]);
        App.state.runsData[runId] = { metrics, config };
    },

    refresh: () => {
        App.refreshData().then(() => {
            const el = document.getElementById('connection-status');
            const original = el.innerHTML;
            el.innerHTML = '<span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span> Refreshing';
            setTimeout(() => el.innerHTML = original, 1000);
        });
    },

    renderDashboard: () => {
        App.renderSummary();
        App.renderCharts();
        App.renderStats();
        App.renderConfig();

        if (App.state.selectedRuns.size > 0) {
            const lastRun = Array.from(App.state.selectedRuns).pop();
            if (App.state.activeTab === 'artifacts') App.renderArtifactsTab();
        }
    },

    renderSummary: () => {
        const container = document.getElementById('summary-container');
        const runs = Array.from(App.state.selectedRuns);

        if (runs.length === 0) {
            container.innerHTML = '';
            return;
        }

        const runStats = runs.map(runId => {
            const m = App.state.runsData[runId]?.metrics || [];
            if (!m.length) return { id: runId, start: '-', duration: '-' };

            const start = new Date(m[0].timestamp);
            const end = new Date(m[m.length - 1].timestamp);

            // Format start
            const startStr = start.toLocaleString();

            // Calc duration
            const diffMs = end - start;
            const diffSec = Math.floor(diffMs / 1000);
            const hrs = Math.floor(diffSec / 3600);
            const mins = Math.floor((diffSec % 3600) / 60);
            const secs = diffSec % 60;
            const durStr = `${hrs}h ${mins}m ${secs}s`;

            return { id: runId, start: startStr, duration: durStr, steps: m.length };
        });

        if (runs.length === 1) {
            const s = runStats[0];
            container.innerHTML = `
                <div class="card p-4 bg-white flex items-center gap-6 text-sm">
                    <div class="font-semibold text-brand-600">${s.id}</div>
                    <div class="flex gap-2 text-gray-600"><span class="font-medium">Started:</span> ${s.start}</div>
                    <div class="flex gap-2 text-gray-600"><span class="font-medium">Duration:</span> ${s.duration}</div>
                    <div class="flex gap-2 text-gray-600"><span class="font-medium">Steps:</span> ${s.steps}</div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="card bg-white overflow-hidden">
                    <table class="w-full text-sm text-left text-gray-500">
                        <thead class="text-xs text-gray-700 uppercase bg-gray-50">
                            <tr>
                                <th class="px-4 py-2">Run</th>
                                <th class="px-4 py-2">Started</th>
                                <th class="px-4 py-2">Duration</th>
                                <th class="px-4 py-2">Steps</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${runStats.map(s => `
                                <tr class="border-b last:border-0 hover:bg-gray-50">
                                    <td class="px-4 py-2 font-medium text-brand-600">${s.id}</td>
                                    <td class="px-4 py-2">${s.start}</td>
                                    <td class="px-4 py-2">${s.duration}</td>
                                    <td class="px-4 py-2">${s.steps}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
    },

    renderStats: () => {
        const runs = Array.from(App.state.selectedRuns);
        if (runs.length === 0) {
            document.getElementById('stats-container').innerHTML = '';
            return;
        }
        // Last run stats
        const runId = runs[runs.length - 1];
        const data = App.state.runsData[runId];
        if (!data || !data.metrics.length) return;

        const lastStep = data.metrics[data.metrics.length - 1];
        const keys = Object.keys(lastStep).filter(k => typeof lastStep[k] === 'number' && k !== 'step');

        document.getElementById('stats-container').innerHTML = keys.slice(0, 4).map(k => `
            <div class="card p-4 bg-white border-l-4 border-brand-500">
                <div class="text-xs text-gray-500 uppercase font-semibold mb-1">${k}</div>
                <div class="text-2xl font-bold text-gray-800">${lastStep[k].toFixed(4)}</div>
                <div class="text-xs text-brand-600 mt-1">Run: ${runId}</div>
            </div>
        `).join('');
    },

    renderCharts: () => {
        const container = document.getElementById('charts-container');
        const runs = Array.from(App.state.selectedRuns);

        if (runs.length === 0) {
            container.innerHTML = `
                <div class="col-span-1 xl:col-span-2 card p-8 text-center text-gray-400 min-h-[400px] flex items-center justify-center">
                    Select a run to view metrics
                </div>`;
            return;
        }

        const allKeys = new Set();
        runs.forEach(r => {
            const m = App.state.runsData[r]?.metrics;
            if (m && m.length) {
                Object.keys(m[0]).forEach(k => {
                    if (k !== 'step' && k !== 'timestamp' && typeof m[0][k] === 'number') allKeys.add(k);
                });
            }
        });

        container.innerHTML = '';

        const slider = document.getElementById('plot-size-slider');
        const initialSize = slider ? slider.value : 300;
        const initialHeight = Math.round(initialSize * 1.0); // Square aspect ratio

        allKeys.forEach(metric => {
            const div = document.createElement('div');
            div.className = 'card p-4 bg-white shadow-sm overflow-hidden';
            div.style.minHeight = `${initialHeight}px`;
            div.style.height = `${initialHeight}px`; // Force height for ratio
            container.appendChild(div);

            const traces = runs.map((runId, idx) => {
                const m = App.state.runsData[runId]?.metrics || [];
                const colors = ['#2563eb', '#16a34a', '#dc2626', '#d97706', '#9333ea', '#0891b2'];

                return {
                    x: m.map(d => d.step || 0),
                    y: m.map(d => d[metric]),
                    type: 'scatter',
                    mode: 'lines',
                    name: runId,
                    line: { shape: 'spline', width: 2, color: colors[idx % colors.length] }
                };
            });

            const titleCasedMetric = App._toTitleCase(metric);

            const layout = {
                title: {
                    text: titleCasedMetric,
                    font: { family: 'Inter', size: 16, color: '#1e293b' },
                    x: 0.01,
                    xanchor: 'left'
                },
                autosize: true,
                margin: { l: 60, r: 40, t: 60, b: 80 }, // Increased right and bottom margins
                showlegend: true,
                legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center', bgcolor: 'rgba(255,255,255,0)' }, // Adjusted legend position
                xaxis: {
                    title: 'Step',
                    titlefont: { size: 12, color: '#64748b' },
                    tickfont: { size: 11, color: '#64748b' },
                    gridcolor: '#f1f5f9'
                },
                yaxis: {
                    title: titleCasedMetric,
                    titlefont: { size: 12, color: '#64748b' },
                    tickfont: { size: 11, color: '#64748b' },
                    gridcolor: '#f1f5f9'
                },
                font: { family: 'Inter' },
                hovermode: 'x unified',
                plot_bgcolor: '#ffffff',
                paper_bgcolor: '#ffffff',
            };

            const config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: [
                    'lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d',
                    'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines'
                ],
                toImageButtonOptions: {
                    format: 'png',
                    filename: `${metric}_plot`,
                    height: 500,
                    width: 500, // Square export
                    scale: 2
                }
            };
            Plotly.newPlot(div, traces, layout, config);
        });
    },

    _toTitleCase: (str) => {
        return str.replace(/_/g, ' ').replace(/\w\S*/g, (txt) => {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    },

    renderConfig: () => {
        const container = document.querySelector('#tab-config .card');
        const runs = Array.from(App.state.selectedRuns);

        if (runs.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-400 mt-20">Select runs to compare configurations</div>';
            return;
        }

        container.innerHTML = `
            <table class="w-full text-sm text-left text-gray-500">
                <thead class="text-xs text-gray-700 uppercase bg-gray-50 sticky top-0">
                    <tr>
                        <th class="px-6 py-3">Parameter</th>
                        ${runs.map(r => `<th class="px-6 py-3">${r}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${App._generateConfigRows(runs)}
                </tbody>
            </table>
        `;
    },

    _generateConfigRows: (runs) => {
        const keys = new Set();
        runs.forEach(r => Object.keys(App.state.runsData[r]?.config || {}).forEach(k => keys.add(k)));
        return Array.from(keys).map(k => `
            <tr class="bg-white border-b hover:bg-gray-50">
                <td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">${k}</td>
                ${runs.map(r => {
            const val = App.state.runsData[r]?.config?.[k] || '-';
            return `<td class="px-6 py-4">${val}</td>`;
        }).join('')}
            </tr>
        `).join('');
    },



    renderArtifactsTab: async () => {
        const container = document.getElementById('artifact-list');
        const runs = Array.from(App.state.selectedRuns);

        if (runs.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-400 text-sm mt-10">Select a run to browse artifacts</div>';
            return;
        }

        container.innerHTML = '<div class="text-xs text-gray-400 p-2">Loading...</div>';
        const htmlParts = [];

        for (const runId of runs) {
            try {
                const res = await fetch(`/api/experiments/${App.state.currentExperiment}/runs/${runId}/artifacts_list`);
                const files = await res.json();

                // Run Header
                htmlParts.push(`
                    <div class="px-2 py-1 bg-brand-50 border-y border-brand-100 text-xs font-bold text-brand-700 mt-2 first:mt-0 sticky top-0 z-10">
                        ${runId}
                    </div>
                `);

                if (!files.length) {
                    htmlParts.push('<div class="text-xs text-gray-400 p-2 italic">No artifacts found.</div>');
                    continue;
                }

                const fileHtml = files.map(f => `
                    <div class="flex items-center gap-2 p-2 hover:bg-gray-100 rounded cursor-pointer group text-sm border-b border-transparent hover:border-gray-100"
                         onclick="App.previewArtifact('${runId}', '${f.path}', '${f.type}')">
                         <i class="${App._getFileIcon(f.type)} text-gray-500"></i>
                         <span class="truncate text-gray-700">${f.name}</span>
                         <span class="text-gray-400 text-xs ml-auto">${(f.size / 1024).toFixed(1)} KB</span>
                    </div>
                `).join('');

                htmlParts.push(fileHtml);

            } catch (e) {
                htmlParts.push(`<div class="text-red-500 p-2 text-xs">Failed to load artifacts for ${runId}</div>`);
            }
        }

        container.innerHTML = htmlParts.join('');
    },

    _getFileIcon: (ext) => {
        if (['.png', '.jpg', '.jpeg', '.svg'].includes(ext)) return 'ri-image-line';
        if (['.parquet', '.csv'].includes(ext)) return 'ri-table-line';
        if (['.yaml', '.json', '.yml'].includes(ext)) return 'ri-code-line';
        if (['.log', '.txt'].includes(ext)) return 'ri-file-text-line';
        if (['.mp4'].includes(ext)) return 'ri-movie-line';
        return 'ri-file-line';
    },

    previewArtifact: async (runId, path, type) => {
        const container = document.getElementById('artifact-preview');
        const title = document.getElementById('preview-filename');
        const downloadBtn = document.getElementById('preview-download');

        title.innerText = path;
        title.title = path; // Tooltip for long names

        const url = `/api/experiments/${App.state.currentExperiment}/runs/${runId}/artifacts/content?path=${encodeURIComponent(path)}`;

        // Setup Download Button
        downloadBtn.href = url;
        downloadBtn.classList.remove('hidden');

        container.innerHTML = '<div class="loader"></div>';

        // Reset zoom state if needed (though we rebuild container)

        if (['.png', '.jpg', '.jpeg', '.svg'].includes(type.toLowerCase())) {
            container.innerHTML = `
                <div class="w-full h-full flex items-center justify-center overflow-hidden bg-gray-100 relative group">
                     <div class="absolute top-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                        Scroll to Zoom • Drag to Pan
                     </div>
                    <img src="${url}" class="max-w-none transition-transform duration-75 ease-out origin-center" style="transform: scale(1) translate(0px, 0px);" id="preview-image" />
                </div>
            `;
            // Attach Zoom Handler
            const img = document.getElementById('preview-image');
            App.attachZoomHandler(img.parentElement, img);

        } else if (['.mp4'].includes(type)) {
            container.innerHTML = `<video controls class="max-w-full max-h-full"><source src="${url}" type="video/mp4"></video>`;
        } else if (['.parquet', '.csv'].includes(type)) {
            try {
                const res = await fetch(url);
                const json = await res.json();
                if (json.error) throw json.error;

                // Render Simple Table
                const cols = json.columns;
                const rows = json.data;
                const table = `
                    <div class="w-full h-full overflow-auto">
                    <table class="w-full text-xs text-left text-gray-500 border-collapse">
                        <thead class="text-xs text-gray-700 uppercase bg-gray-50 sticky top-0 shadow-sm z-10">
                            <tr>${cols.map(c => `<th class="px-4 py-2 border-b bg-gray-50">${c}</th>`).join('')}</tr>
                        </thead>
                        <tbody>
                            ${rows.map(r => `
                                <tr class="bg-white border-b hover:bg-gray-50">
                                    ${cols.map(c => `<td class="px-4 py-2 font-mono whitespace-nowrap">${r[c] !== null ? r[c] : ''}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    </div>
                `;
                container.innerHTML = table;
            } catch (e) {
                container.innerHTML = `<div class="text-red-500">Error reading data: ${e}</div>`;
            }
        } else if (['.yaml', '.yml', '.json', '.log', '.txt'].includes(type)) {
            // Fetch text content and display
            try {
                const res = await fetch(url);
                if (!res.ok) throw "Failed to load file";
                const text = await res.text();

                container.innerHTML = `
                    <div class="w-full h-full overflow-auto bg-white p-4">
                        <pre class="font-mono text-xs whitespace-pre-wrap text-gray-700">${App._escapeHtml(text)}</pre>
                    </div>
                `;
            } catch (e) {
                container.innerHTML = `<div class="text-red-500">Error reading file: ${e}</div>`;
            }
        } else {
            // Fallback
            container.innerHTML = `
                <div class="text-center text-gray-400 mt-20">
                    <div class="mb-2"><i class="ri-file-download-line text-4xl"></i></div>
                    Preview not available for this file type.
                </div>
             `;
        }
    },

    attachZoomHandler: (container, target) => {
        let scale = 1;
        let panning = false;
        let pointX = 0;
        let pointY = 0;
        let startX = 0;
        let startY = 0;

        const updateTransform = () => {
            target.style.transform = `translate(${pointX}px, ${pointY}px) scale(${scale})`;
        };

        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            const xs = (e.offsetX - pointX) / scale;
            const ys = (e.offsetY - pointY) / scale;
            const delta = -Math.sign(e.deltaY);
            if (delta > 0) scale *= 1.1;
            else scale /= 1.1;

            // Limit scale
            scale = Math.min(Math.max(0.1, scale), 10);

            pointX = e.offsetX - xs * scale;
            pointY = e.offsetY - ys * scale;

            updateTransform();
        });

        container.addEventListener('mousedown', (e) => {
            e.preventDefault();
            startX = e.clientX - pointX;
            startY = e.clientY - pointY;
            panning = true;
            container.style.cursor = 'grabbing';
        });

        container.addEventListener('mouseup', (e) => {
            panning = false;
            container.style.cursor = 'default';
        });

        container.addEventListener('mouseleave', (e) => {
            panning = false;
            container.style.cursor = 'default';
        });

        container.addEventListener('mousemove', (e) => {
            e.preventDefault();
            if (!panning) return;
            pointX = e.clientX - startX;
            pointY = e.clientY - startY;
            updateTransform();
        });
    },

    _escapeHtml: (text) => {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
};

document.addEventListener('DOMContentLoaded', App.init);
window.app = App;
