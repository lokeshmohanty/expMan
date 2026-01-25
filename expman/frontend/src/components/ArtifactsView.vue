<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useExperimentStore } from '../stores/experiment'

const props = defineProps({
  runId: {
    type: String,
    required: true
  }
})

const store = useExperimentStore()
const selectedFile = ref(null)
const fileContent = ref(null)
const isLoadingContent = ref(false)

const artifacts = computed(() => {
  return store.runsData[props.runId]?.artifacts || []
})

// Group files by directory structure or just flat list?
// Flat list with relative paths is returned by API, let's just use that for now.

async function selectFile(file) {
  selectedFile.value = file
  fileContent.value = null
  isLoadingContent.value = true

  try {
    const url = `/api/experiments/${store.currentExperiment}/runs/${props.runId}/artifacts/content?path=${encodeURIComponent(file.path)}`
    
    // For images, we just use the URL
    if (['.png', '.jpg', '.jpeg', '.svg', '.gif'].includes(file.type)) {
      fileContent.value = url
    } 
    // For data files (json, text, yaml, log)
    else if (['.json', '.yaml', '.yml', '.txt', '.log'].includes(file.type)) {
        const res = await fetch(url)
        fileContent.value = await res.text()
    }
    // For Parquet/CSV - API returns JSON representation
    else if (['.parquet', '.csv'].includes(file.type)) {
        const res = await fetch(url)
        fileContent.value = await res.json()
    }
    else {
        // Unknown type download link?
        fileContent.value = null
    }

  } catch (e) {
    console.error("Failed to load file content", e)
    fileContent.value = "Error loading content"
  } finally {
    isLoadingContent.value = false
  }
}

const isImage = computed(() => {
    if (!selectedFile.value) return false
    return ['.png', '.jpg', '.jpeg', '.svg', '.gif'].includes(selectedFile.value.type)
})

const isTable = computed(() => {
    if (!selectedFile.value) return false
    return ['.parquet', '.csv'].includes(selectedFile.value.type)
})

// Fetch artifacts on mount
onMounted(() => {
    store.fetchArtifacts(props.runId)
})
</script>

<template>
  <div class="flex h-[500px] border rounded-lg overflow-hidden bg-white">
    <!-- File List -->
    <div class="w-1/3 border-r bg-slate-50 overflow-y-auto">
      <div v-if="artifacts.length === 0" class="p-4 text-slate-400 text-sm text-center">
        No artifacts found
      </div>
      <div 
        v-for="file in artifacts" 
        :key="file.path"
        @click="selectFile(file)"
        class="p-3 border-b border-slate-100 cursor-pointer hover:bg-white transition-colors text-sm flex items-center gap-2"
        :class="{'bg-blue-50 border-l-4 border-l-blue-500': selectedFile?.path === file.path}"
      >
        <i class="ri-file-line text-slate-400"></i>
        <div class="truncate">
            {{ file.name }}
            <div class="text-[10px] text-slate-400">{{ file.size }} bytes</div>
        </div>
      </div>
    </div>

    <!-- Preview Area -->
    <div class="flex-1 overflow-auto p-4 bg-slate-100 relative">
        <div v-if="isLoadingContent" class="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>

        <div v-if="!selectedFile" class="h-full flex items-center justify-center text-slate-400">
            Select a file to preview
        </div>

        <template v-else>
            <!-- Image Preview -->
            <div v-if="isImage" class="h-full flex items-center justify-center">
                <img :src="fileContent" class="max-w-full max-h-full object-contain rounded shadow-sm" />
            </div>

            <!-- Table Preview (Parquet/CSV) -->
            <div v-else-if="isTable && fileContent?.data" class="overflow-auto bg-white rounded shadow-sm">
                <table class="w-full text-sm text-left">
                    <thead class="bg-slate-50 text-slate-600 font-medium">
                        <tr>
                            <th v-for="col in fileContent.columns" :key="col" class="p-2 border-b">{{ col }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(row, idx) in fileContent.data" :key="idx" class="border-b last:border-0 hover:bg-slate-50">
                            <td v-for="col in fileContent.columns" :key="col" class="p-2 text-slate-700">
                                {{ row[col] }}
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div class="p-2 text-xs text-slate-400 text-center bg-slate-50 border-t">
                    Showing first 100 rows
                </div>
            </div>

            <!-- Text/Code Preview -->
            <div v-else-if="fileContent && typeof fileContent === 'string'" class="bg-slate-900 rounded-lg p-4 font-mono text-sm overflow-auto h-full">
                <!-- Check if it looks like a log file -->
                <template v-if="selectedFile.type === '.log' || selectedFile.type === '.txt'">
                    <div v-for="(line, idx) in fileContent.split('\n')" :key="idx" class="whitespace-pre">
                        <span 
                            :class="{
                                'text-blue-400': line.includes('INFO'),
                                'text-yellow-400': line.includes('WARNING') || line.includes('WARN'),
                                'text-red-500': line.includes('ERROR') || line.includes('CRITICAL') || line.includes('EXCEPTION'),
                                'text-gray-400': line.includes('DEBUG'),
                                'text-slate-200': !line.match(/INFO|WARN|ERROR|CRITICAL|DEBUG/)
                            }"
                        >{{ line }}</span>
                    </div>
                </template>
                <div v-else class="whitespace-pre-wrap text-slate-200">
                    {{ fileContent }}
                </div>
            </div>

            <!-- Fallback -->
            <div v-else class="text-center text-slate-500 mt-10">
                Preview not available for this file type.
            </div>
        </template>
    </div>
  </div>
</template>
