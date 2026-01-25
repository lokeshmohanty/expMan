<script setup>
import { useExperimentStore } from '../stores/experiment'

const store = useExperimentStore()
</script>

<template>
  <div class="flex flex-col h-full bg-slate-900 text-slate-300">
    <!-- Header -->
    <div class="p-4 border-b border-slate-700">
      <h1 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <i class="ri-flask-fill text-brand-500"></i> ExpMan
      </h1>
      
      <select 
        class="w-full bg-slate-800 border-none text-sm rounded p-2 focus:ring-1 focus:ring-brand-500"
        :value="store.currentExperiment"
        @change="store.selectExperiment($event.target.value)"
      >
        <option :value="null" disabled>Select Experiment</option>
        <option v-for="exp in store.experiments" :key="exp" :value="exp">
          {{ exp }}
        </option>
      </select>
    </div>

    <!-- Runs List -->
    <div class="flex-1 overflow-y-auto p-2 space-y-1">
      <div v-if="!store.currentExperiment" class="text-xs text-slate-500 text-center mt-4">
        No experiment selected
      </div>
      
      <div 
        v-for="run in store.runs" 
        :key="run"
        @click="store.toggleRun(run)"
        class="flex items-center justify-between p-2 rounded cursor-pointer hover:bg-slate-800 transition-colors group"
        :class="{'bg-slate-800': store.selectedRuns.has(run)}"
      >
        <div class="flex items-center gap-2">
          <!-- Checkbox UI -->
          <div 
            class="w-4 h-4 rounded border flex items-center justify-center transition-colors"
            :class="[
              store.selectedRuns.has(run) ? 'bg-brand-600 border-brand-600' : 'border-slate-600'
            ]"
          >
            <i v-if="store.selectedRuns.has(run)" class="ri-check-line text-white text-xs"></i>
          </div>
          <span class="text-sm truncate max-w-[140px]" :class="{'text-white': store.selectedRuns.has(run)}">{{ run }}</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="p-4 border-t border-slate-700 text-xs text-slate-500 flex justify-between items-center">
      <span>Vue 3 Dashboard</span>
      <span v-if="store.selectedRuns.size > 0">
        {{ store.selectedRuns.size }} selected
      </span>
    </div>
  </div>
</template>
