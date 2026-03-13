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

    <!-- AI 配置 -->
    <a-card style="margin-top: 20px;">
      <template #title>
        <a-space>
          <icon-settings />
          AI 配置
        </a-space>
      </template>
      <a-form
        :model="aiConfigForm"
        layout="vertical"
      >
        <a-form-item label="MiniMax API Key">
          <a-input-password
            v-model="aiConfigForm.apiKey"
            placeholder="请输入 MiniMax API Key"
            allow-clear
          />
          <template #help>
            <div v-if="aiConfigForm.originalKey" style="color: var(--color-text-3);">
            当前 Key：{{ aiConfigForm.originalKey }}
            </div>
          </template>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" :loading="aiLoading" @click="saveAiConfig">
            保存 AI 配置
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getUserInfo, updateUserInfo, uploadAvatar } from '@/api/user'
import http from '@/api/http'

const router = useRouter()
const loading = ref(false)
const fileList = ref([])
const aiLoading = ref(false)

const form = ref({
  username: '',
  nickname: '',
  email: '',
  avatar: ''
})

const aiConfigForm = ref({
  apiKey: '',
  originalKey: ''
})

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

// 获取 AI 配置
const fetchAiConfig = async () => {
  try {
    const res = await http.get('/wx/configs', {
      params: { limit: 100, offset: 0 }
    })
    const configs = (res as any).list || []
    const aiKeyConfig = configs.find((item: any) => item.config_key === 'minimax.api_key')
    if (aiKeyConfig && aiKeyConfig.config_value) {
      const key = aiKeyConfig.config_value
      // 脱敏显示：保留前10位，后面的用*代替
      aiConfigForm.value.originalKey = key.length > 10 ? key.substring(0, 10) + '****' + key.substring(key.length - 4) : key
    }
  } catch (error) {
    console.error('获取AI配置失败:', error)
  }
}

// 保存 AI 配置
const saveAiConfig = async () => {
  if (!aiConfigForm.value.apiKey) {
    Message.warning('请输入 API Key')
    return
  }
  aiLoading.value = true
  try {
    await http.post('/wx/configs', {
      config_key: 'minimax.api_key',
      config_value: aiConfigForm.value.apiKey
    })
    Message.success('AI 配置保存成功')
    aiConfigForm.value.apiKey = ''
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
</style>