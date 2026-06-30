<template>
  <div class="skeleton-loading" v-if="loading">
    <div class="skeleton-header">
      <div class="skeleton-title"></div>
    </div>
    <div class="skeleton-content">
      <div class="skeleton-row" v-for="i in rows" :key="i">
        <div class="skeleton-cell" v-for="j in cols" :key="j"></div>
      </div>
    </div>
  </div>
  <slot v-else />
</template>

<script setup>
defineProps({
  loading: Boolean,
  rows: { type: Number, default: 5 },
  cols: { type: Number, default: 4 }
})
</script>

<style scoped>
.skeleton-loading {
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-header {
  margin-bottom: 20px;
}

.skeleton-title {
  height: 32px;
  width: 200px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}

.skeleton-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.skeleton-cell {
  flex: 1;
  height: 40px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

html.dark .skeleton-title,
html.dark .skeleton-cell {
  background: linear-gradient(90deg, #374151 25%, #4b5563 50%, #374151 75%);
}
</style>
