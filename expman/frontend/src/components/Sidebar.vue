<script setup>
import { useExperimentStore } from '../stores/experiment'

const store = useExperimentStore()
</script>

<template>
  <div class="flex flex-col h-full bg-[#fcfaf8] border-r border-[#d5c4a1] text-[#3c3836]">
    <!-- Filter/Search (Replaces Header) -->
    <div class="p-4 border-b border-[#d5c4a1] bg-[#fbf1c7]">
      <div class="text-xs font-semibold uppercase tracking-wider text-[#928374] mb-2">Experiment</div>
      <div class="font-bold text-[#3c3836] truncate mb-3" :title="store.currentExperiment">
        {{ store.currentExperiment }}
      </div>
      
      <!-- Quick Switcher? Or just keep it focused on runs -->
      <button 
        @click="store.currentExperiment = null"
        class="text-xs text-[#d65d0e] hover:text-[#9d0006] flex items-center gap-1 mb-4"
      >
        <i class="ri-arrow-left-line"></i> Back to Experiments
      </button>

      <div class="text-xs font-semibold uppercase tracking-wider text-[#928374] mb-2">Runs</div>
      <!-- Run Filter Input could go here -->
    </div>

    <!-- Runs List -->
    <div class="flex-1 overflow-y-auto p-2 space-y-1 bg-[#f2e5bc]">
      <div v-if="!store.currentExperiment" class="text-xs text-[#928374] text-center mt-4">
        No experiment selected
      </div>
      
      <div 
        v-for="run in store.runs" 
        :key="run"
        @click="store.toggleRun(run)"
        class="flex items-center justify-between p-2 rounded cursor-pointer hover:bg-[#ebdbb2] hover:shadow-sm border border-transparent hover:border-[#d5c4a1] transition-all group"
        :class="{'bg-[#ebdbb2] shadow-sm border-[#d5c4a1]': store.selectedRuns.has(run)}"
      >
        <div class="flex items-center gap-2 w-full">
          <!-- Checkbox UI -->
          <div 
            class="w-4 h-4 rounded border flex items-center justify-center transition-colors flex-shrink-0"
            :class="[
              store.selectedRuns.has(run) ? 'bg-[#d65d0e] border-[#d65d0e]' : 'border-[#a89984] bg-[#fbf1c7]'
            ]"
          >
            <i v-if="store.selectedRuns.has(run)" class="ri-check-line text-[#fbf1c7] text-xs"></i>
          </div>
          <span class="text-sm truncate text-[#3c3836] font-medium" :class="{'text-[#282828]': store.selectedRuns.has(run)}">{{ run }}</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="p-4 border-t border-[#d5c4a1] bg-[#fbf1c7] text-xs text-[#928374] flex justify-between items-center shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.02)]">
      <span>ExpMan</span>
      <span v-if="store.selectedRuns.size > 0" class="text-[#d65d0e] font-medium">
        {{ store.selectedRuns.size }} selected
      </span>
    </div>
  </div>
</template>
