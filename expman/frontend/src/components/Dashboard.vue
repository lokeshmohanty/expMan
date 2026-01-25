<script setup>
import { onMounted, onUnmounted, ref, watch, nextTick, computed } from 'vue'; // Added computed
import { useExperimentStore } from '../stores/experiment';
import Plotly from 'plotly.js-dist-min';
import ArtifactsView from './ArtifactsView.vue';
import ConfigView from './ConfigView.vue';
import RunSummaryTable from './RunSummaryTable.vue';

const store = useExperimentStore();
const chartsContainer = ref(null);
let pollingInterval = null;

// Tabs
const tabs = ['Metrics', 'Artifacts', 'Config'];
const currentTab = ref('Metrics');

// Metadata Editing (Global handled by App)
// Metadata Editing (Global handled by App)
// const experimentMetadata = ref({}); // Moved to store

const emit = defineEmits(['edit-metadata'])

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

// Watch current experiment change to fetch stats and metadata
watch(() => store.currentExperiment, async (newVal) => {
    if(newVal) {
        store.fetchExperimentStats(newVal)
        store.fetchExperimentMetadata(newVal)
    }
}, { immediate: true })

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

const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

function formatTime(isoString) {
    if (!isoString) return 'Unknown'
    const d = new Date(isoString)
    const day = d.getDate()
    const month = months[d.getMonth()]
    const year = d.getFullYear()
    const wday = days[d.getDay()]
    const h = d.getHours().toString().padStart(2,'0')
    const m = d.getMinutes().toString().padStart(2,'0')
    const s = d.getSeconds().toString().padStart(2,'0')
    return `${h}:${m}:${s} - ${day} ${month}, ${year} (${wday})`
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
      margin: { l: 60, r: 20, t: 40, b: 50 },
      showlegend: true,
      legend: { orientation: 'h', y: -0.2 },
      font: { family: 'Inter, sans-serif', color: '#3c3836' },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      xaxis: {
        title: 'Step',
        gridcolor: '#d5c4a1'
      },
      yaxis: {
        title: metric,
        gridcolor: '#d5c4a1'
      },
      modebar: {
        bgcolor: 'rgba(0,0,0,0)',
        color: '#d65d0e',
        activecolor: '#af3a03'
      }
    };
    
    const config = { 
        responsive: true, 
        displayModeBar: true, 
        displaylogo: false,
        modeBarButtons: [['toImage', 'pan2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']]
    };

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
      <div class="px-6 py-4 flex flex-shrink-0 justify-between items-center border-b border-[#d5c4a1] bg-[#fbf1c7]">
          <div>
            <div class="flex items-baseline gap-3">
                 <h2 class="text-2xl font-bold text-[#3c3836]">
                    {{ store.experimentMetadata.display_name || store.currentExperiment }}
                 </h2>
                 <button @click="emit('edit-metadata', {id: store.currentExperiment})" class="text-xs text-[#d65d0e] hover:underline">
                    <i class="ri-edit-line"></i> Edit
                 </button>
            </div>
            <p v-if="store.experimentMetadata.description" class="text-sm text-[#504945] mt-1">
                {{ store.experimentMetadata.description }}
            </p>
            <div v-if="store.selectedRuns.size === 0" class="text-sm text-[#7c6f64] mt-1">
                Select runs from the sidebar to visualize.
            </div>
          </div>
          
          <!-- Tab Navigation -->
          <div class="flex bg-[#ebdbb2] p-1 rounded-lg">
              <button 
                v-for="tab in tabs" 
                :key="tab"
                @click="currentTab = tab"
                class="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
                :class="currentTab === tab ? 'bg-[#fbf1c7] text-[#d65d0e] shadow-sm' : 'text-[#504945] hover:text-[#3c3836]'"
              >
                  {{ tab }}
              </button>
          </div>
      </div>

    <!-- Main Content Area -->
    <div class="flex-1 overflow-y-auto p-6 relative bg-[#fbf1c7]">
        
        <!-- Experiment Summary (When no runs selected) -->
        <div v-show="store.selectedRuns.size === 0" class="space-y-6">
             <div class="bg-[#f2e5bc] border border-[#d5c4a1] rounded-lg p-4">
                <h3 class="font-bold text-[#b57614]">Experiment Overview</h3>
                <p class="text-[#7c6f64] text-sm mt-1">
                    {{ store.currentExperiment }} contains {{ store.experimentStats.length }} runs. 
                    Select runs from the table below or the sidebar to compare them.
                </p>
             </div>
             <RunSummaryTable />
        </div>

        <!-- Metrics View (When runs selected) -->
        <div v-show="store.selectedRuns.size > 0 && currentTab === 'Metrics'" ref="chartsContainer" class="pb-20">
            <!-- Run Meta Info Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                <div 
                    v-for="runId in store.selectedRuns" 
                    :key="runId" 
                    class="bg-[#f2e5bc] p-3 rounded-lg shadow-sm border border-[#d5c4a1] flex items-center justify-between"
                >
                     <div>
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full" :style="{backgroundColor: store.getRunColor(runId)}"></span>
                            <span class="font-semibold text-[#3c3836]">{{ runId }}</span>
                        </div>
                        <div class="text-xs text-[#504945] mt-1 pl-5">
                            Created: {{ formatTime(store.runsData[runId]?.config?.created || store.experimentStats.find(s => s.run === runId)?.created) }} 
                        </div>
                     </div>
                </div>
            </div>

            <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div 
                    v-for="metric in metricKeys" 
                    :key="metric" 
                    class="bg-[#f2e5bc] p-4 rounded-xl shadow-sm border border-[#d5c4a1]"
                >
                    <div :id="`chart-${metric}`" class="w-full"></div>
                </div>
            </div>
            
            <div v-if="metricKeys.size === 0" class="text-center py-20 text-[#928374]">
                No metrics found for selected runs.
            </div>
        </div>

        <!-- Artifacts View -->
        <div v-if="currentTab === 'Artifacts'" class="space-y-8 pb-20">
            <div v-for="runId in store.selectedRuns" :key="runId" class="space-y-2">
                <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full" :style="{backgroundColor: store.getRunColor(runId)}"></span>
                    <h3 class="font-semibold text-lg text-[#3c3836]">{{ runId }}</h3>
                </div>
                <ArtifactsView :runId="runId" />
            </div>
            <div v-if="store.selectedRuns.size === 0" class="text-center py-20 text-[#928374]">
                 Select a run to view artifacts.
            </div>
        </div>

        <!-- Config View -->
        <div v-if="currentTab === 'Config'" class="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
            <div v-for="runId in store.selectedRuns" :key="runId" class="flex flex-col gap-2">
                 <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full" :style="{backgroundColor: store.getRunColor(runId)}"></span>
                    <h3 class="font-semibold text-lg text-[#3c3836]">{{ runId }}</h3>
                </div>
                <ConfigView :runId="runId" />
            </div>
             <div v-if="store.selectedRuns.size === 0" class="col-span-full text-center py-20 text-[#928374]">
                 Select a run to view configuration.
            </div>
        </div>
    </div>

    <!-- Metadata Edit Modal -->
    <div v-if="isEditingMetadata" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-[#fbf1c7] p-6 rounded-lg w-full max-w-md border border-[#d5c4a1] shadow-xl">
            <h3 class="text-lg font-bold text-[#3c3836] mb-4">Edit Experiment Details</h3>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-[#504945] mb-1">Display Name</label>
                    <input v-model="editForm.display_name" class="w-full p-2 rounded bg-[#f2e5bc] border border-[#d5c4a1] focus:border-[#d65d0e] outline-none text-[#3c3836]" />
                </div>
                <div>
                    <label class="block text-sm font-medium text-[#504945] mb-1">Description</label>
                    <textarea v-model="editForm.description" rows="3" class="w-full p-2 rounded bg-[#f2e5bc] border border-[#d5c4a1] focus:border-[#d65d0e] outline-none text-[#3c3836]"></textarea>
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <button @click="isEditingMetadata = false" class="px-4 py-2 text-sm text-[#504945] hover:text-[#3c3836]">Cancel</button>
                <button @click="saveMetadata" class="px-4 py-2 bg-[#d65d0e] text-[#fbf1c7] rounded hover:bg-[#c3510d] text-sm font-semibold">Save</button>
            </div>
        </div>
    </div>

  </div>
</template>
