<template>
  <div class="edit-user">
    <a-page-header
      title="修改个人信息"
      subtitle="更新您的账户信息"
      :show-back="true"
      @back="goBack"
    />

    <a-card>
      <a-form
        :model="form"
        :rules="rules"
        @submit="handleSubmit"
        layout="vertical"
      >
        <a-form-item label="头像">
          <a-upload
            :custom-request="handleUploadChange"
            :file-list="fileList"
            :show-file-list="false"
            accept="image/*"
            :limit="1"
            :max-size="2048"
            @exceed="handleExceed"
            @error="handleUploadError"
          >
            <template #upload-button>
              <div class="avatar-upload">
                <a-avatar :size="80">
                  <img
                    v-if="form.avatar"
                    :src="form.avatar"
                    alt="avatar"
                    @error="handleImageError"
                  >
                  <icon-user v-else />
                </a-avatar>
                <div class="upload-mask">
                  <icon-edit />
                </div>
              </div>
            </template>
          </a-upload>
        </a-form-item>

        <a-form-item label="用户名" field="username">
          <a-input
            v-model="form.username"
            placeholder="请输入用户名"
            allow-clear
          >
            <template #prefix><icon-user /></template>
          </a-input>
        </a-form-item>

        <a-form-item label="昵称" field="nickname">
          <a-input
            v-model="form.nickname"
            placeholder="请输入昵称"
            allow-clear
          >
            <template #prefix><icon-user /></template>
          </a-input>
        </a-form-item>

        <a-form-item label="邮箱" field="email">
          <a-input
            v-model="form.email"
            placeholder="请输入邮箱"
            allow-clear
          >
            <template #prefix><icon-email /></template>
          </a-input>
        </a-form-item>

        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="loading">
              保存修改
            </a-button>
            <a-button @click="resetForm">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- AI 配置 - 多模型列表 -->
    <a-card style="margin-top: 20px;">
      <template #title>
        <a-space>
          <icon-settings />
          AI 模型配置
        </a-space>
      </template>

      <div class="model-list">
        <div
          v-for="model in modelList"
          :key="model.id"
          class="model-card"
          :class="{ 'is-active': model.isActive }"
        >
          <!-- 模型卡片头部 -->
          <div class="model-card-header">
            <div class="model-name">
              <span>{{ model.modelName }}</span>
              <a-tag v-if="model.isActive" color="green">当前生效</a-tag>
            </div>
            <a-switch
              v-model="model.isActive"
              checked-color="#165dff"
              @change="(checked: boolean) => handleModelActiveChange(model.id, checked)"
            />
          </div>

          <!-- API Key 输入 -->
          <div class="model-card-body">
            <a-form-item label="API Key">
              <a-input
                v-model="model.apiKey"
                :type="showKeys[model.id] ? 'text' : 'password'"
                placeholder="请输入 API Key"
                allow-clear
                @focus="editingModelId = model.id"
                @blur="editingModelId = null"
              >
                <template #suffix>
                  <a-button
                    type="text"
                    size="mini"
                    @click="toggleShowKey(model.id)"
                  >
                    <icon-eye v-if="showKeys[model.id]" />
                    <icon-eye-invisible v-else />
                  </a-button>
                </template>
              </a-input>
            </a-form-item>
          </div>
        </div>
      </div>

      <!-- 全局保存按钮 -->
      <a-form-item class="save-button-wrapper">
        <a-button type="primary" :loading="aiLoading" @click="saveAiConfig">
          保存 AI 配置
        </a-button>
      </a-form-item>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getUserInfo, updateUserInfo, uploadAvatar } from '@/api/user'
import http from '@/api/http'

// 模型数据类型
interface ModelConfig {
  id: string
  modelName: string
  apiKey: string
  originalKey: string
  isActive: boolean
  configKey: string
  enabledKey: string
}

const router = useRouter()
const loading = ref(false)
const fileList = ref([])
const aiLoading = ref(false)
const editingModelId = ref<string | null>(null)
const showKeys = reactive<Record<string, boolean>>({})

const form = ref({
  username: '',
  nickname: '',
  email: '',
  avatar: ''
})

// 模型列表 - 初始状态
const modelList = ref<ModelConfig[]>([
  {
    id: 'minimax',
    modelName: 'MiniMax',
    apiKey: '',
    originalKey: '',
    isActive: true,
    configKey: 'minimax.api_key',
    enabledKey: 'minimax.enabled'
  },
  {
    id: 'deepseek',
    modelName: 'DeepSeek',
    apiKey: '',
    originalKey: '',
    isActive: false,
    configKey: 'deepseek.api_key',
    enabledKey: 'deepseek.enabled'
  }
])

const rules = {
  username: [{ required: true, message: '请输入用户名' }],
  email: [
    { required: true, message: '请输入邮箱' },
    { type: 'email', message: '请输入有效的邮箱地址' }
  ]
}

const handleUploadChange = async (options: any) => {
  const file = options.fileItem?.file || options.file
  
  // 文件类型验证
  if (!file?.type?.startsWith('image/')) {
    Message.error('请选择图片文件 (JPEG/PNG)')
    return
  }

  // 文件大小验证 (2MB)
  if (file.size > 2 * 1024 * 1024) {
    Message.error('图片大小不能超过2MB')
    return
  }

  try {
    const res = await uploadAvatar(file)
    form.value.avatar = res.avatar
  } catch (error) {
    console.error('上传错误:', error)
    Message.error(`上传失败: ${error.response?.data?.message || error.message || '服务器错误'}`)
  } 
  return false
}

const handleExceed = () => {
  Message.warning('只能上传一个头像文件')
}

const handleUploadError = (error: Error) => {
  Message.error(`上传出错: ${error.message || '文件上传失败'}`)
}

const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement
  img.src = '/default-avatar.png'
}

const fetchUserInfo = async () => {
  loading.value = true
  try {
    const res = await getUserInfo()
    form.value = {
      username: res.username,
      nickname: res.nickname || res.username,
      email: res.email || '',
      avatar: res.avatar 
    }
  } catch (error) {
    router.push('/login')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
    let response=await updateUserInfo(form.value)
    if (response.code === 0){
      Message.success(response?.message || '更新成功')
    }
}

const resetForm = () => {
  fetchUserInfo()
}

const goBack = () => {
  router.go(-1)
}

// 脱敏显示 API Key
const maskKey = (key: string): string => {
  if (!key) return ''
  if (key.length < 8) return '****'
  return key.slice(0, 8) + '****' + key.slice(-4)
}

// 切换显示 API Key
const toggleShowKey = (modelId: string) => {
  showKeys[modelId] = !showKeys[modelId]
}

// 切换模型启用状态（互斥逻辑）
const handleModelActiveChange = (modelId: string, checked: boolean) => {
  if (checked) {
    // 启用当前模型时，禁用其他所有模型
    modelList.value.forEach(m => {
      if (m.id !== modelId) {
        m.isActive = false
      }
    })
  }
}

// 获取 AI 配置
const fetchAiConfig = async () => {
  try {
    const res = await http.get('/wx/configs', {
      params: { limit: 100, offset: 0 }
    })
    const configs = (res as any).list || []

    // 遍历模型列表获取配置
    for (const model of modelList.value) {
      // 获取 API Key
      const keyConfig = configs.find((item: any) => item.config_key === model.configKey)
      if (keyConfig && keyConfig.config_value) {
        model.originalKey = keyConfig.config_value
        model.apiKey = keyConfig.config_value // 同步到 apiKey 用于显示和编辑
      }

      // 获取启用状态
      const enabledConfig = configs.find((item: any) => item.config_key === model.enabledKey)
      if (enabledConfig && enabledConfig.config_value) {
        model.isActive = enabledConfig.config_value === 'true'
      }
    }
  } catch (error) {
    console.error('获取AI配置失败:', error)
  }
}

// 保存 AI 配置
const saveAiConfig = async () => {
  // 检查是否有启用的模型且配置了 API Key
  const activeModel = modelList.value.find(m => m.isActive)
  if (!activeModel) {
    Message.warning('请至少启用一个模型')
    return
  }

  if (!activeModel.apiKey && !activeModel.originalKey) {
    Message.warning(`请为 ${activeModel.modelName} 配置 API Key`)
    return
  }

  aiLoading.value = true
  try {
    // 保存每个模型的配置
    for (const model of modelList.value) {
      // 保存 API Key（如果有新输入）
      if (model.apiKey) {
        await http.post('/wx/configs', {
          config_key: model.configKey,
          config_value: model.apiKey
        })
        model.originalKey = model.apiKey
        model.apiKey = '' // 清空输入框
      }

      // 保存启用状态
      await http.post('/wx/configs', {
        config_key: model.enabledKey,
        config_value: model.isActive ? 'true' : 'false'
      })
    }

    Message.success('AI 配置保存成功')
    fetchAiConfig()
  } catch (error) {
    Message.error('保存失败')
  } finally {
    aiLoading.value = false
  }
}

onMounted(() => {
  fetchUserInfo()
  fetchAiConfig()
})
</script>

<style scoped>
.edit-user {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.avatar-upload {
  position: relative;
  width: 80px;
  height: 80px;
  cursor: pointer;
}

.upload-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.avatar-upload:hover .upload-mask {
  opacity: 1;
}

.arco-form-item {
  margin-bottom: 20px;
}

/* AI 模型列表样式 */
.model-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.model-card {
  border: 2px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
  overflow: hidden;
}

.model-card:hover {
  border-color: var(--color-primary-3);
}

.model-card.is-active {
  border-color: #165dff;
  background-color: rgba(22, 93, 255, 0.05);
}

.model-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.model-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.model-card-body {
  padding: 0 4px;
}

.save-button-wrapper {
  margin-top: 24px;
}
</style>