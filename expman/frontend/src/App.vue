<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Dashboard from './components/Dashboard.vue'
import { useExperimentStore } from './stores/experiment'

const store = useExperimentStore()

onMounted(() => {
  store.fetchExperiments()
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-slate-50">
    <!-- Sidebar -->
    <Sidebar class="w-64 flex-shrink-0 border-r border-slate-200 bg-white" />

    <!-- Main Content -->
    <main class="flex-1 overflow-auto relative">
      <Dashboard v-if="store.currentExperiment" />
      <div v-else class="flex items-center justify-center h-full text-slate-400">
        <div class="text-center">
          <i class="ri-flask-line text-5xl mb-4 block"></i>
          <p class="text-lg">Select an experiment to begin</p>
        </div>
      </div>
    </main>
  </div>
</template>
