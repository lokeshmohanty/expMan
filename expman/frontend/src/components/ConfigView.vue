<script setup>
import { computed } from 'vue'
import { useExperimentStore } from '../stores/experiment'

const props = defineProps({
  runId: {
    type: String,
    required: true
  }
})

const store = useExperimentStore()

const config = computed(() => {
  return store.runsData[props.runId]?.config || {}
})
</script>

<template>
  <div class="bg-slate-900 rounded-lg p-4 overflow-auto max-h-[500px]">
    <pre class="text-slate-200 font-mono text-sm leading-relaxed">{{ JSON.stringify(config, null, 2) }}</pre>
  </div>
</template>
