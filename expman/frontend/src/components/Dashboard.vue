<script setup>
import { onMounted, onUnmounted, ref, watch, nextTick } from 'vue';
import { useExperimentStore } from '../stores/experiment';
import Plotly from 'plotly.js-dist-min';
import ArtifactsView from './ArtifactsView.vue';
import ConfigView from './ConfigView.vue';

const store = useExperimentStore();
const chartsContainer = ref(null);
let pollingInterval = null;

// Tabs
const tabs = ['Metrics', 'Artifacts', 'Config'];
const currentTab = ref('Metrics');

// Derived list of all unique metric keys from selected runs
const metricKeys = ref(new Set());

// Watch for data changes to update charts
watch(
  () => [store.selectedRuns, store.runsData, currentTab.value],
  async () => {
    if (currentTab.value === 'Metrics') {
        updateMetricKeys();
        await nextTick();
        renderCharts();
    }
  },
  { deep: true }
);

function updateMetricKeys() {
  const keys = new Set();
  for (const runId of store.selectedRuns) {
    const data = store.runsData[runId];
    if (data?.metrics?.length > 0) {
      // Check first metric entry for keys
      Object.keys(data.metrics[0]).forEach((k) => {
        if (k !== 'step' && k !== 'timestamp' && typeof data.metrics[0][k] === 'number') {
          keys.add(k);
        }
      });
    }
  }
  metricKeys.value = keys;
}

function renderCharts() {
  if (!chartsContainer.value) return;

  // Clear or Update Chart Divs
  // We opt to re-render for simplicity, or use Plotly.react for efficiency
  
  metricKeys.value.forEach((metric) => {
    const divId = `chart-${metric}`;
    let el = document.getElementById(divId);
    
    // Create container if not exists
    if (!el) return; // Should be handled by v-for in template

    const traces = [];
    for (const runId of store.selectedRuns) {
      const data = store.runsData[runId];
      if (!data?.metrics) continue;

      traces.push({
        x: data.metrics.map(m => m.step ?? m.timestamp), // Use step or timestamp
        y: data.metrics.map(m => m[metric]),
        type: 'scatter',
        mode: 'lines',
        name: runId,
        line: { color: store.getRunColor(runId), width: 2 }
      });
    }

    const layout = {
      title: metric.charAt(0).toUpperCase() + metric.slice(1),
      autosize: true,
      height: 350,
      margin: { l: 50, r: 20, t: 40, b: 40 },
      showlegend: true,
      legend: { orientation: 'h', y: -0.2 },
      font: { family: 'Inter, sans-serif' }
    };
    
    const config = { responsive: true, displayModeBar: false };

    Plotly.react(el, traces, layout, config);
  });
}

onMounted(() => {
  // Start Polling only if live mode is enabled
  if (store.serverConfig.live_mode) {
      pollingInterval = setInterval(() => {
        store.refreshAll();
      }, 2000); // Poll every 2s
  }
});

onUnmounted(() => {
  if (pollingInterval) clearInterval(pollingInterval);
});
</script>

<template>
  <div class="flex flex-col h-full overflow-hidden">
      <!-- Top Bar -->
      <div class="px-6 py-4 flex flex-shrink-0 justify-between items-center border-b border-slate-200 bg-white">
          <div>
            <h2 class="text-2xl font-bold text-slate-800">{{ store.currentExperiment }}</h2>
            <div v-if="store.selectedRuns.size === 0" class="text-sm text-slate-500">
                Select runs from the sidebar to visualize.
            </div>
          </div>
          
          <!-- Tab Navigation -->
          <div class="flex bg-slate-100 p-1 rounded-lg">
              <button 
                v-for="tab in tabs" 
                :key="tab"
                @click="currentTab = tab"
                class="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
                :class="currentTab === tab ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
              >
                  {{ tab }}
              </button>
          </div>
      </div>

    <!-- Main Content Area -->
    <div class="flex-1 overflow-y-auto p-6 relative">
        <!-- Metrics View -->
        <div v-show="currentTab === 'Metrics'" ref="chartsContainer" class="grid grid-cols-1 xl:grid-cols-2 gap-6 pb-20">
            <div 
                v-for="metric in metricKeys" 
                :key="metric" 
                class="bg-white p-4 rounded-xl shadow-sm border border-slate-100"
            >
                <div :id="`chart-${metric}`" class="w-full"></div>
            </div>
            
            <div v-if="metricKeys.size === 0 && store.selectedRuns.size > 0" class="col-span-full text-center py-20 text-slate-400">
                No metrics found for selected runs.
            </div>
        </div>

        <!-- Artifacts View -->
        <div v-if="currentTab === 'Artifacts'" class="space-y-8 pb-20">
            <div v-for="runId in store.selectedRuns" :key="runId" class="space-y-2">
                <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full" :style="{backgroundColor: store.getRunColor(runId)}"></span>
                    <h3 class="font-semibold text-lg text-slate-800">{{ runId }}</h3>
                </div>
                <ArtifactsView :runId="runId" />
            </div>
            <div v-if="store.selectedRuns.size === 0" class="text-center py-20 text-slate-400">
                 Select a run to view artifacts.
            </div>
        </div>

        <!-- Config View -->
        <div v-if="currentTab === 'Config'" class="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
            <div v-for="runId in store.selectedRuns" :key="runId" class="flex flex-col gap-2">
                 <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full" :style="{backgroundColor: store.getRunColor(runId)}"></span>
                    <h3 class="font-semibold text-lg text-slate-800">{{ runId }}</h3>
                </div>
                <ConfigView :runId="runId" />
            </div>
             <div v-if="store.selectedRuns.size === 0" class="col-span-full text-center py-20 text-slate-400">
                 Select a run to view configuration.
            </div>
        </div>
    </div>
  </div>
</template>
