<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Dashboard from './components/Dashboard.vue'
import ExperimentList from './components/ExperimentList.vue'
import { useExperimentStore } from './stores/experiment'

const store = useExperimentStore()
const isEditing = ref(false)
const editTarget = ref(null) // {id, display_name, description}
const editForm = ref({ display_name: '', description: '' })

function openEdit(exp) {
    // Exp is {id, display_name}
    editTarget.value = exp
    // Fetch description to fill form
    fetch(`/api/experiments/${exp.id}/metadata`)
        .then(res => {
            if (!res.ok) throw new Error("Metadata fetch failed")
            return res.json()
        })
        .then(data => {
            editForm.value = {
                display_name: data.display_name || exp.id,
                description: data.description || ''
            }
            isEditing.value = true
        })
        .catch(err => {
            console.warn("Failed to fetch metadata, using default", err)
            editForm.value = {
                display_name: exp.display_name || exp.id,
                description: ''
            }
            isEditing.value = true
        })
}

async function saveMetadata() {
    if (!editTarget.value) return
    try {
        const res = await fetch(`/api/experiments/${editTarget.value.id}/metadata`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(editForm.value)
        })
        if (res.ok) {
            isEditing.value = false
            store.fetchExperiments() // Refresh list
            if (store.currentExperiment === editTarget.value.id) {
                store.fetchExperimentStats(store.currentExperiment)
                store.fetchExperimentMetadata(store.currentExperiment)
            }
        }
    } catch(e) {
        alert("Failed to save")
    }
}

onMounted(() => {
  store.fetchExperiments()
})
</script>

<template>
  <div class="flex flex-col h-screen overflow-hidden bg-[#fbf1c7] text-[#3c3836] font-sans">
    <!-- Global Header -->
    <header class="h-14 bg-[#3c3836] text-[#ebdbb2] flex items-center px-6 shadow-sm flex-shrink-0 justify-between relative">
      <!-- Left: Logo/Home -->
      <div 
        class="flex items-center gap-2 cursor-pointer hover:text-white transition-colors"
        @click="store.currentExperiment = null"
      >
        <i class="ri-flask-fill text-[#d65d0e] text-xl"></i> 
        <h1 class="font-bold text-lg tracking-wide">ExpMan</h1>
      </div>
      
      <!-- Center: Title -->
      <div class="absolute left-1/2 transform -translate-x-1/2 font-medium text-lg">
        Experiment Manager
      </div>

      <!-- Right: Links -->
      <div class="flex items-center gap-4">
          <a href="https://github.com/lokeshmohanty/expMan" target="_blank" class="text-[#a89984] hover:text-[#ebdbb2] transition-colors">
            <i class="ri-github-fill text-xl"></i>
          </a>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <Sidebar v-if="store.currentExperiment" class="w-64 flex-shrink-0 border-r border-[#d5c4a1] bg-[#fbf1c7]" />

      <!-- Main Content -->
      <main class="flex-1 overflow-auto relative">
        <Dashboard 
            v-if="store.currentExperiment" 
            @edit-metadata="openEdit"
        />
        <ExperimentList 
            v-else 
            @edit-metadata="openEdit"
        />
      </main>
    </div>

    <!-- Global Edit Modal -->
    <div v-if="isEditing" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-[#fbf1c7] p-6 rounded-lg w-full max-w-md border border-[#d5c4a1] shadow-xl">
            <h3 class="text-lg font-bold text-[#3c3836] mb-4">Edit Experiment: {{ editTarget?.id }}</h3>
            
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
                <button @click="isEditing = false" class="px-4 py-2 text-sm text-[#504945] hover:text-[#3c3836]">Cancel</button>
                <button @click="saveMetadata" class="px-4 py-2 bg-[#d65d0e] text-[#fbf1c7] rounded hover:bg-[#c3510d] text-sm font-semibold">Save</button>
            </div>
        </div>
    </div>
  </div>
</template>
