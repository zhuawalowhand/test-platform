<template>
  <div class="assertion-editor">
    <div class="editor-header">
      <span class="editor-title">高级断言规则</span>
      <div class="editor-actions">
        <el-button size="small" @click="showRaw = !showRaw">
          {{ showRaw ? '表单模式' : 'JSON 模式' }}
        </el-button>
        <el-button size="small" type="primary" @click="addAssertion">
          <el-icon><Plus /></el-icon>添加断言
        </el-button>
      </div>
    </div>

    <!-- JSON 原始模式 -->
    <div v-if="showRaw">
      <el-input
        :model-value="modelValue"
        type="textarea"
        :rows="6"
        placeholder='[{"type":"body_contains","target":"","expected":"成功"}]'
        @input="handleRawInput"
      />
      <div class="form-tip">
        JSON 数组，支持: body_contains, body_not_contains, body_json, header, header_contains, response_time, body_regex
      </div>
    </div>

    <!-- 表单可视化模式 -->
    <div v-else>
      <el-empty v-if="assertions.length === 0" description="暂无断言规则，点击上方按钮添加" :image-size="60" />

      <div v-for="(item, index) in assertions" :key="index" class="assertion-row">
        <div class="row-number">{{ index + 1 }}</div>
        <div class="row-fields">
          <!-- 断言类型 -->
          <el-select v-model="item.type" placeholder="断言类型" style="width: 160px" @change="onTypeChange(item)">
            <el-option
              v-for="t in assertionTypes"
              :key="t.value"
              :label="t.label"
              :value="t.value"
            />
          </el-select>

          <!-- 目标字段 -->
          <el-input
            v-if="showTarget(item.type)"
            v-model="item.target"
            :placeholder="getTargetPlaceholder(item.type)"
            style="flex: 1"
          />

          <!-- 操作符（仅 response_time） -->
          <el-select
            v-if="item.type === 'response_time'"
            v-model="item.operator"
            style="width: 70px"
          >
            <el-option label="<" value="<" />
            <el-option label="≤" value="<=" />
            <el-option label=">" value=">" />
            <el-option label="≥" value=">=" />
          </el-select>

          <!-- 预期值 -->
          <el-input
            v-if="showExpected(item.type)"
            v-model="item.expected"
            :placeholder="getExpectedPlaceholder(item.type)"
            :style="{ width: item.type === 'response_time' ? '120px' : '160px' }"
          />
        </div>
        <el-button size="small" type="danger" :icon="Delete" circle @click="removeAssertion(index)" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { Delete } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])

const showRaw = ref(false)

const assertionTypes = [
  { value: 'body_contains', label: '响应体包含' },
  { value: 'body_not_contains', label: '响应体不包含' },
  { value: 'body_json', label: 'JSON 路径值' },
  { value: 'header', label: 'Header 等于' },
  { value: 'header_contains', label: 'Header 包含' },
  { value: 'response_time', label: '响应时间' },
  { value: 'body_regex', label: '正则匹配' },
]

const assertions = ref([])

// 从 modelValue 解析
const parseValue = (val) => {
  if (!val) return []
  try {
    const parsed = JSON.parse(val)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

// 初始化
assertions.value = parseValue(props.modelValue)

// 监听外部变化
watch(() => props.modelValue, (val) => {
  const parsed = parseValue(val)
  // 避免循环更新：只在内容不同时更新
  if (JSON.stringify(parsed) !== JSON.stringify(assertions.value)) {
    assertions.value = parsed
  }
})

// 监听内部变化，同步到 modelValue
watch(assertions, (val) => {
  if (val.length === 0) {
    emit('update:modelValue', '')
  } else {
    emit('update:modelValue', JSON.stringify(val, null, 2))
  }
}, { deep: true })

const addAssertion = () => {
  assertions.value.push({
    type: 'body_contains',
    target: '',
    expected: '',
    operator: '<'
  })
}

const removeAssertion = (index) => {
  assertions.value.splice(index, 1)
}

const onTypeChange = (item) => {
  // 切换类型时重置字段
  item.target = ''
  item.expected = ''
  if (item.type === 'response_time') {
    item.operator = '<'
    item.expected = '3000'
  }
}

const showTarget = (type) => {
  return !['response_time'].includes(type)
}

const showExpected = (type) => {
  return !['body_regex'].includes(type)
    // body_regex 的 expected 不显示，target 就是正则
}

const getTargetPlaceholder = (type) => {
  const map = {
    body_contains: '要搜索的文本',
    body_not_contains: '不应包含的文本',
    body_json: 'JSON 路径，如 data.user.name',
    header: 'Header 名称，如 Content-Type',
    header_contains: 'Header 名称，如 Content-Type',
    body_regex: '正则表达式，如 \\d{3}-\\d{4}',
  }
  return map[type] || ''
}

const getExpectedPlaceholder = (type) => {
  const map = {
    body_contains: '预期包含的文本',
    body_not_contains: '不应包含的文本',
    body_json: '预期值',
    header: '预期完整值',
    header_contains: '预期包含文本',
    response_time: '毫秒数',
  }
  return map[type] || '预期值'
}

const handleRawInput = (val) => {
  emit('update:modelValue', val)
}
</script>

<style scoped>
.assertion-editor {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  background: #fafafa;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.editor-title {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.editor-actions {
  display: flex;
  gap: 6px;
}

.assertion-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  margin-bottom: 8px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.row-number {
  min-width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  background: #f0f2f5;
  border-radius: 50%;
  font-size: 12px;
  color: #909399;
}

.row-fields {
  display: flex;
  gap: 8px;
  flex: 1;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

html.dark .assertion-editor {
  background: #1d1e1f;
  border-color: #4c4d4f;
}

html.dark .assertion-row {
  background: #262727;
  border-color: #4c4d4f;
}

html.dark .row-number {
  background: #374151;
  color: #9ca3af;
}
</style>
