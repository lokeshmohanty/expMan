import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useExperimentStore = defineStore('experiment', () => {
    // State
    const experiments = ref([])
    const currentExperiment = ref(null)
    const runs = ref([])
    const selectedRuns = ref(new Set())
    const serverConfig = ref({ live_mode: true }) // Default to true until fetched

    // Cache: runId -> { metrics: [], config: {}, artifacts: [], lastStep: -1 }
    const runsData = ref({})

    // Actions
    async function fetchExperiments() {
        // Also fetch config when fetching experiments
        await fetchServerConfig()

        try {
            const res = await fetch('/api/experiments')
            experiments.value = await res.json()
        } catch (e) {
            console.error("Failed to fetch experiments", e)
        }
    }

    async function fetchServerConfig() {
        try {
            const res = await fetch('/api/config')
            serverConfig.value = await res.json()
        } catch (e) {
            console.error("Failed to fetch server config", e)
        }
    }

    async function selectExperiment(name) {
        currentExperiment.value = name
        selectedRuns.value.clear()
        runsData.value = {}
        await fetchRuns(name)
    }

    async function fetchRuns(name) {
        if (!name) return
        try {
            const res = await fetch(`/api/experiments/${name}/runs`)
            runs.value = await res.json()
        } catch (e) {
            console.error("Failed to fetch runs", e)
        }
    }

    async function toggleRun(runId) {
        if (selectedRuns.value.has(runId)) {
            selectedRuns.value.delete(runId)
        } else {
            selectedRuns.value.add(runId)
            await loadRunData(runId)
        }
    }

    async function loadRunData(runId) {
        if (!currentExperiment.value) return

        // Initialize cache entry if missing
        if (!runsData.value[runId]) {
            runsData.value[runId] = { metrics: [], config: {}, artifacts: [], lastStep: -1 }
            // Fetch Config once
            try {
                const res = await fetch(`/api/experiments/${currentExperiment.value}/runs/${runId}/config`)
                runsData.value[runId].config = await res.json()
            } catch (e) {
                console.error(`Failed to load config for ${runId}`, e)
            }
        }

        // Fetch Metrics (Incremental)
        const cached = runsData.value[runId]
        const since = cached.lastStep

        try {
            let url = `/api/experiments/${currentExperiment.value}/runs/${runId}/metrics`
            if (since !== null && since !== undefined && since >= 0) {
                url += `?since_step=${since}`
            }

            const res = await fetch(url)
            const newMetrics = await res.json()

            if (newMetrics.length > 0) {
                cached.metrics = [...cached.metrics, ...newMetrics]
                // Update lastStep based on the last received metric
                const last = newMetrics[newMetrics.length - 1]
                if (last.step !== undefined) {
                    cached.lastStep = last.step
                }
            }
        } catch (e) {
            console.error(`Failed to load metrics for ${runId}`, e)
        }
    }

    async function refreshAll() {
        if (!currentExperiment.value) return

        // Refresh runs list (to catch new runs)
        await fetchRuns(currentExperiment.value)

        // Refresh data for selected runs
        for (const runId of selectedRuns.value) {
            await loadRunData(runId)
            await fetchArtifacts(runId)
        }
    }

    async function fetchArtifacts(runId) {
        if (!currentExperiment.value) return
        try {
            const res = await fetch(`/api/experiments/${currentExperiment.value}/runs/${runId}/artifacts_list`)
            const files = await res.json()
            if (runsData.value[runId]) {
                runsData.value[runId].artifacts = files
            }
        } catch (e) {
            console.error(`Failed to fetch artifacts for ${runId}`, e)
        }
    }

    // Getters
    const getRunColor = (runId) => {
        // Simple hash-based color or rotation
        const colors = ['#2563eb', '#16a34a', '#dc2626', '#d97706', '#9333ea', '#0891b2']
        let hash = 0
        for (let i = 0; i < runId.length; i++) {
            hash = runId.charCodeAt(i) + ((hash << 5) - hash)
        }
        return colors[Math.abs(hash) % colors.length]
    }

    // State for experiment overview stats
    const experimentStats = ref([])
    const experimentMetadata = ref({})

    async function fetchExperimentStats(name) {
        if (!name) return
        try {
            const res = await fetch(`/api/experiments/${name}/stats`)
            experimentStats.value = await res.json()
        } catch (e) {
            console.error("Failed to fetch experiment stats", e)
        }
    }

    async function fetchExperimentMetadata(name) {
        if (!name) return
        try {
            const res = await fetch(`/api/experiments/${name}/metadata`)
            experimentMetadata.value = await res.json()
        } catch (e) {
            console.error("Failed to fetch experiment metadata", e)
        }
    }

    return {
        experiments,
        currentExperiment,
        runs,
        selectedRuns,
        serverConfig,
        runsData,
        experimentStats,
        experimentMetadata,
        fetchExperiments,
        selectExperiment,
        fetchRuns,
        fetchExperimentStats,
        fetchExperimentMetadata,
        toggleRun,
        refreshAll,
        getRunColor,
        fetchArtifacts
    }
})
