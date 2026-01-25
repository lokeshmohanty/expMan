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
onMounted(async () => {
    await store.fetchArtifacts(props.runId)
    // Auto select run.log
    if (!selectedFile.value && artifacts.value.length > 0) {
        const logFile = artifacts.value.find(f => f.name === 'run.log')
        if (logFile) {
            selectFile(logFile)
        }
    }
})
</script>

<template>
  <div class="flex h-[500px] border border-[#d5c4a1] rounded-lg overflow-hidden bg-[#fbf1c7]">
    <!-- File List -->
    <div class="w-1/3 border-r border-[#d5c4a1] bg-[#ebdbb2] overflow-y-auto">
      <div v-if="artifacts.length === 0" class="p-4 text-[#928374] text-sm text-center">
        No artifacts found
      </div>
      <div 
        v-for="file in artifacts" 
        :key="file.path"
        @click="selectFile(file)"
        class="p-3 border-b border-[#d5c4a1] cursor-pointer hover:bg-[#fbf1c7] transition-colors text-sm flex items-center gap-2"
        :class="{'bg-[#f2e5bc] border-l-4 border-l-[#d65d0e]': selectedFile?.path === file.path}"
      >
        <i class="ri-file-line text-[#7c6f64]"></i>
        <div class="truncate text-[#3c3836]">
            {{ file.name }}
            <div class="text-[10px] text-[#7c6f64]">{{ file.size }} bytes</div>
        </div>
        
        <!-- Download Icon in List -->
        <a 
           :href="`/api/experiments/${store.currentExperiment}/runs/${runId}/artifacts/content?path=${encodeURIComponent(file.path)}`" 
           download
           @click.stop
           title="Download"
           class="ml-auto text-[#d65d0e] hover:text-[#9d0006] p-1.5 rounded hover:bg-[#ebdbb2] transition-colors"
        >
           <i class="fa-solid fa-download"></i>
        </a>
      </div>
    </div>

    <!-- Preview Area -->
    <div class="flex-1 overflow-auto p-4 bg-[#fbf1c7] relative">
        <div v-if="isLoadingContent" class="absolute inset-0 flex items-center justify-center bg-[#fbf1c7]/50 z-10">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d65d0e]"></div>
        </div>

        <div v-if="!selectedFile" class="h-full flex items-center justify-center text-[#928374]">
            Select a file to preview
        </div>

        <template v-else>
            <!-- Image Preview -->
            <div v-if="isImage" class="h-full flex items-center justify-center">
                <img :src="fileContent" class="max-w-full max-h-full object-contain rounded shadow-sm" />
            </div>

            <!-- Table Preview (Parquet/CSV) -->
            <div v-else-if="isTable && fileContent?.data" class="overflow-auto bg-white rounded shadow-sm border border-[#d5c4a1] h-full flex flex-col">
                <div class="overflow-x-auto flex-1">
                    <table class="w-full text-sm text-left whitespace-nowrap">
                        <thead class="bg-[#ebdbb2] text-[#3c3836] font-medium border-b border-[#d5c4a1] sticky top-0 z-10">
                            <tr>
                                <th v-for="col in fileContent.columns" :key="col" class="p-2 border-b border-[#d5c4a1]">{{ col }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(row, idx) in fileContent.data" :key="idx" class="border-b border-[#d5c4a1] last:border-0 even:bg-[#fbf1c7] hover:bg-[#d5c4a1] transition-colors">
                                <td v-for="col in fileContent.columns" :key="col" class="p-2 text-[#3c3836]">
                                    {{ row[col] }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="p-2 text-xs text-[#7c6f64] text-center bg-[#ebdbb2] border-t border-[#d5c4a1] flex-shrink-0">
                    Showing first 100 rows
                </div>
            </div>

            <!-- Text/Code Preview -->
            <div v-else-if="fileContent && typeof fileContent === 'string'" class="bg-[#282828] rounded-lg p-4 font-mono text-sm overflow-auto h-full border border-[#d5c4a1] text-[#ebdbb2]">
                <!-- Check if it looks like a log file -->
                <template v-if="selectedFile.type === '.log' || selectedFile.type === '.txt'">
                    <div v-for="(line, idx) in fileContent.split('\n')" :key="idx" class="whitespace-pre">
                        <span 
                            :class="{
                                'text-[#83a598]': line.includes('INFO'),
                                'text-[#fabd2f]': line.includes('WARNING') || line.includes('WARN'),
                                'text-[#fb4934]': line.includes('ERROR') || line.includes('CRITICAL') || line.includes('EXCEPTION'),
                                'text-[#928374]': line.includes('DEBUG'),
                                'text-[#ebdbb2]': !line.match(/INFO|WARN|ERROR|CRITICAL|DEBUG/)
                            }"
                        >{{ line }}</span>
                    </div>
                </template>
                <div v-else class="whitespace-pre-wrap text-[#ebdbb2]">
                    {{ fileContent }}
                </div>
            </div>

            <!-- Fallback -->
            <div v-else class="text-center text-[#928374] mt-10">
                Preview not available for this file type.
            </div>
        </template>
    </div>
  </div>
</template>
