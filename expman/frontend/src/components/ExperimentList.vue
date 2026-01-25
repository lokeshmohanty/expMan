<script setup>
import { ref } from 'vue'
import { useExperimentStore } from '../stores/experiment'

const store = useExperimentStore()
const emit = defineEmits(['edit-metadata'])

function openEditModal(exp) {
    // We can emit to App/Dashboard or handle here. 
    // Ideally the store or parent handles the "active editing" experiment.
    // For now, let's just use the store's currentExperiment concept? 
    // Actually user can edit without selecting.
    // Let's emit an event to open the modal which we moved to Dashboard... Wait, Dashboard is only active when experiment selected.
    // We need a global modal or a local one here.
    // Let's create a local editing state here for simplicity or reuse the component?
    // User asked for "option to edit... from the UI".
    // If we are in the list, we assume we want to edit specific exp.
    emit('edit-metadata', exp)
}
</script>

<template>
  <div class="p-8 max-w-7xl mx-auto">
    <div class="mb-8 text-center">
      <h2 class="text-3xl font-bold text-[#3c3836] mb-2">Welcome to ExpMan</h2>
      <p class="text-[#504945]">Select an experiment to view results and manage artifacts.</p>
    </div>

    <div v-if="store.experiments.length === 0" class="text-center py-20 bg-[#fbf1c7] rounded-xl shadow-sm border border-[#d5c4a1]">
      <div class="text-[#928374] mb-4">
        <i class="ri-flask-line text-6xl"></i>
      </div>
      <p class="text-lg text-[#504945]">No experiments found.</p>
      <p class="text-sm text-[#7c6f64] mt-2">Run an experiment to see it here.</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="exp in store.experiments" 
        :key="exp.id"
        class="bg-[#fbf1c7] rounded-xl shadow-sm border border-[#d5c4a1] p-6 relative hover:shadow-md hover:border-[#d65d0e] transition-all group"
      >
        <!-- Clickable Area -->
        <div @click="store.selectExperiment(exp.id)" class="cursor-pointer">
            <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-lg bg-[#ebdbb2] flex items-center justify-center text-[#d65d0e] group-hover:bg-[#d65d0e] group-hover:text-[#fbf1c7] transition-colors">
                <i class="ri-flask-fill text-2xl"></i>
            </div>
            <!-- Arrow hidden by default? Or keep it. -->
            <i class="ri-arrow-right-line text-[#a89984] group-hover:text-[#d65d0e] transition-colors"></i>
            </div>
            
            <h3 class="text-xl font-bold text-[#3c3836] mb-2 group-hover:text-[#b57614] transition-colors pr-6">
                {{ exp.display_name }}
            </h3>
            <p class="text-xs text-[#928374] font-mono mb-2" v-if="exp.display_name !== exp.id">ID: {{ exp.id }}</p>
            <p class="text-sm text-[#504945]">Click to view runs and analysis.</p>
        </div>

        <!-- Edit Menu Trigger (3 dots) -->
        <div class="absolute top-4 right-4 z-10">
             <button @click.stop="openEditModal(exp)" class="text-[#928374] hover:text-[#d65d0e] p-1 rounded hover:bg-[#ebdbb2]">
                <i class="ri-more-2-fill text-xl"></i>
             </button>
        </div>
      </div>
    </div>
  </div>
</template>
