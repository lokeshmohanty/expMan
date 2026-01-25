<script setup>
import { computed } from 'vue'
import { useExperimentStore } from '../stores/experiment'

const store = useExperimentStore()

// We assume stats are already fetched when this component is mounted/needed 
// or dashboard needs to fetch it.
const stats = computed(() => store.experimentStats)

const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

function formatTime(isoString) {
    if (!isoString) return '-'
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

function getDuration(stat) {
    // If backend provided duration, use it
    if (stat.duration) return stat.duration
    return '-'
}
</script>

<template>
  <div class="bg-[#fbf1c7] rounded-xl shadow-sm border border-[#d5c4a1] overflow-hidden">
     <div class="overflow-x-auto">
        <table class="w-full text-sm text-left">
            <thead class="bg-[#ebdbb2] text-[#3c3836] font-semibold border-b border-[#d5c4a1]">
                <tr>
                    <th class="px-6 py-4">Run Name</th>
                    <th class="px-6 py-4">Created</th>
                    <th class="px-6 py-4">Duration</th>
                    <template v-if="stats.length > 0">
                        <th v-for="key in Object.keys(stats[0]).filter(k => !['run', 'created', 'step', 'timestamp', 'duration'].includes(k)).slice(0, 5)" :key="key" class="px-6 py-4 capitalize">
                            {{ key }}
                        </th>
                    </template>
                </tr>
            </thead>
            <tbody class="divide-y divide-[#d5c4a1]">
                <tr 
                    v-for="stat in stats" 
                    :key="stat.run" 
                    class="hover:bg-[#f2e5bc] transition-colors cursor-pointer group"
                    @click="store.toggleRun(stat.run)"
                >
                    <td class="px-6 py-4 font-medium text-[#3c3836] flex items-center gap-3">
                        <div 
                             class="w-4 h-4 rounded border flex items-center justify-center transition-colors"
                             :class="[
                               store.selectedRuns.has(stat.run) ? 'bg-[#d65d0e] border-[#d65d0e]' : 'border-[#bdae93]'
                             ]"
                        >
                             <i v-if="store.selectedRuns.has(stat.run)" class="ri-check-line text-[#fbf1c7] text-xs"></i>
                        </div>
                        {{ stat.run }}
                    </td>
                    <td class="px-6 py-4 text-[#504945] whitespace-nowrap">
                        {{ formatTime(stat.created) }}
                    </td>
                    <td class="px-6 py-4 text-[#504945] whitespace-nowrap font-mono text-xs">
                        {{ getDuration(stat) }}
                    </td>
                    
                    <template v-if="stats.length > 0">
                         <td v-for="key in Object.keys(stats[0]).filter(k => !['run', 'created', 'step', 'timestamp', 'duration'].includes(k)).slice(0, 5)" :key="key" class="px-6 py-4 text-[#504945]">
                            {{ typeof stat[key] === 'number' ? stat[key].toFixed(4) : stat[key] }}
                        </td>
                    </template>
                </tr>
            </tbody>
        </table>
        
        <div v-if="stats.length === 0" class="text-center py-10 text-[#928374]">
            No runs found.
        </div>
     </div>
  </div>
</template>
