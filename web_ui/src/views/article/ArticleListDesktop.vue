<template>
  <a-spin :loading="fullLoading" tip="正在刷新..." size="large">
    <a-layout class="article-list">
      
      <a-layout-sider :width="300"
        :style="{ background: '#fff', padding: '0', borderRight: '1px solid #eee', display: 'flex', flexDirection: 'column', border: 0 }">
        <a-card :bordered="false" title="公众号"
          :headStyle="{ padding: '12px 16px', borderBottom: '1px solid #eee', background: '#fff', zIndex: 1, border: 0 }">
          <template #extra>
            <a-dropdown>
              <a-button type="primary">
                <template #icon><icon-plus /></template>
                订阅
                <icon-down />
              </a-button>
              <template #content>
                <a-doption @click="showAddModal"><template #icon><icon-plus /></template>添加公众号</a-doption>
                <a-doption @click="exportMPS"><template #icon><icon-export /></template>导出公众号</a-doption>
                <a-doption @click="importMPS"><template #icon><icon-import /></template>导入公众号</a-doption>
                <a-doption @click="exportOPML"><template #icon><icon-share-external /></template>导出OPML</a-doption>
              </template>
            </a-dropdown>
          </template>
          <div style="display: flex; flex-direction: column;; background: #fff">
            <div style="margin-bottom: 12px;">
              <a-input-search 
                v-model="mpSearchText" 
                placeholder="搜索公众号名称" 
                @search="handleMpSearch" 
                @keyup.enter="handleMpSearch"
                allow-clear 
                size="small" />
            </div>
            <div style="margin-bottom: 8px; padding: 0 8px;">
              <a-radio-group v-model="mpFilterType" type="button" size="small" style="width: 100%;">
                <a-radio value="active" style="flex: 1; text-align: center;">启用</a-radio>
                <a-radio value="disabled" style="flex: 1; text-align: center;">停用</a-radio>
                <a-radio value="all" style="flex: 1; text-align: center;">全部</a-radio>
              </a-radio-group>
            </div>
            <a-list :data="filteredMpList" :loading="mpLoading" bordered>
              <template #item="{ item, index }">
                <a-list-item @click="handleMpClick(item.id)" :class="{ 'active-mp': activeMpId === item.id }"
                  style="padding: 9px 8px; cursor: pointer; display: flex; align-items: center; justify-content: space-between;">
                  <div style="display: flex; align-items: center;">
                    <img :src="Avatar(item.avatar)" width="40" style="float:left;margin-right:1rem;" />
                    <a-typography-text strong style="line-height:32px;" :style="{ opacity: item.status === 0 ? 0.5 : 1 }">
                      {{ item.name || item.mp_name }}
                    </a-typography-text>
                    <a-button v-if="activeMpId === item.id && item.id != ''" size="mini" type="text" status="danger"
                      @click="$event.stopPropagation(); deleteMp(item.id)">
                      <template #icon><icon-delete /></template>
                    </a-button>
                    <a-button v-if="activeMpId === item.id && item.id != ''" size="mini" type="text"
                      @click="$event.stopPropagation(); copyMpId(item.id)">
                      <template #icon><icon-copy /></template>
                    </a-button>
                    <a-button v-if="activeMpId === item.id && item.id != ''" size="mini" type="text"
                      @click="$event.stopPropagation(); toggleMpStatus(item.id, item.status === 1 ? 0 : 1)">
                      <template #icon>
                        <icon-stop v-if="item.status === 1" />
                        <icon-play-arrow v-else />
                      </template>
                    </a-button>
                  </div>
                </a-list-item>
              </template>
            </a-list>
            <a-pagination :total="mpPagination.total" simple @change="handleMpPageChange" :show-total="true"
              style="margin-top: 1rem;" />
          </div>
        </a-card>
      </a-layout-sider>

      <a-layout-content :style="{ padding: '20px', width: '100%' }">
        <a-page-header :title="activeFeed ? activeFeed.name : '全部'" :subtitle="'管理您的公众号订阅内容'" :show-back="false">
          <template #extra>
            <a-space>
              <span style="font-size: 12px; color: var(--color-text-3);">{{ issourceUrl ? '原链接' : '内链' }}</span>
              <a-switch 
                v-model="issourceUrl" 
                size="small" 
                style="margin: 0 8px;">
              </a-switch>

              <a-button  @click="handleExportShow()">
                <template #icon><icon-export /></template>
                导出
              </a-button>
              <ExportModal ref="exportModal"  />
              <a-button @click="refresh" v-if="activeFeed?.id != ''">
                <template #icon><icon-refresh /></template>
                刷新
              </a-button>
              <a-dropdown>
                <a-button v-if="activeFeed?.id == ''">
                  <template #icon><icon-delete /></template>
                  清理
                  <icon-down />
                </a-button>
                <template #content>
                  <a-doption @click="clear_articles">
                    <template #icon> <TextIcon text="E" iconClass="" /></template>
                    清理无效文章
                  </a-doption>
                  <a-doption @click="clear_duplicate_article">
                    <template #icon> <TextIcon text="C" iconClass="" /></template>
                    清理重复文章
                  </a-doption>
                </template>
              </a-dropdown>
              <a-button @click="handleAuthClick">
                <template #icon><icon-scan /></template>
                刷新授权
              </a-button>
              <a-button @click="showAiConfig">
                <template #icon><icon-settings /></template>
                AI配置
              </a-button>
              <a-dropdown>
                <a-button>
                  <template #icon>
                    <IconWifi />
                  </template>
                  订阅
                  <icon-down />
                </a-button>
                <template #content>
                  <a-doption @click="rssFormat = 'atom'; openRssFeed()"><template #icon>
                      <TextIcon text="atom" iconClass="" />
                    </template>ATOM</a-doption>
                  <a-doption @click="rssFormat = 'rss'; openRssFeed()"><template #icon>
                      <TextIcon text="rss" iconClass="" />
                    </template>RSS</a-doption>
                  <a-doption @click="rssFormat = 'json'; openRssFeed()"><template #icon>
                      <TextIcon text="json" iconClass="" />
                    </template>JSON</a-doption>
                  <a-doption @click="rssFormat = 'md'; openRssFeed()"><template #icon>
                      <TextIcon text="md" iconClass="" />
                    </template>Markdown</a-doption>
                  <a-doption @click="rssFormat = 'txt'; openRssFeed()"><template #icon>
                      <TextIcon text="txt" iconClass="" />
                    </template>Text</a-doption>
                </template>
              </a-dropdown>
              <a-button type="primary" status="success" @click="handleBatchAnalyze" :disabled="!selectedRowKeys.length">
                <template #icon><icon-thunderbolt /></template>
                AI分析 <span style="font-size: 8px; opacity: 0.6;">(V16-FINAL-CLEAN)</span>
              </a-button>
              <a-button type="primary" status="danger" @click="handleBatchDelete" :disabled="!selectedRowKeys.length">
                <template #icon><icon-delete /></template>
                批量删除
              </a-button>
            </a-space>
          </template>
        </a-page-header>

        <a-modal v-model:visible="analyzeModalVisible" title="AI 批量分析进度 (V16-FINAL-CLEAN)" :footer="false" :mask-closable="false">
          <div style="margin-bottom: 20px;">
            <a-progress :percent="analyzePercent" :status="analyzeStatus" />
            <div style="margin-top: 10px; text-align: center; font-weight: bold;">{{ analyzeProgressText }}</div>
          </div>
          <div class="log-container" ref="logContainer" style="height: 200px; overflow-y: auto; background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 12px; font-family: monospace;">
            <div v-for="(log, index) in analyzeLogs" :key="index" :style="{ color: log.type === 'error' ? 'red' : 'inherit', marginBottom: '4px' }">
              {{ log.time }} - {{ log.msg }}
            </div>
          </div>
          <div style="margin-top: 20px; text-align: right;">
            <a-button type="primary" :disabled="analyzing" @click="analyzeModalVisible = false">关闭</a-button>
          </div>
        </a-modal>

        <a-card style="border:0">
          <a-alert type="success" closable>{{ activeFeed?.mp_intro || "请选择一个公众号码进行管理,搜索文章后再点击订阅会有惊喜哟！！！" }}</a-alert>
          <div class="search-bar" style="display: flex; gap: 10px; align-items: center; margin-bottom: 16px;">
            <a-range-picker v-model="dateRange" style="width: 260px" @change="handleSearch" allow-clear value-format="YYYY-MM-DD" />
            <a-select v-model="aiCategory" :style="{width:'160px'}" placeholder="AI 分类" allow-clear @change="handleSearch">
              <a-option value="">全部</a-option>
              <a-option v-for="(cfg, cat) in AI_CATEGORY_CONFIG" :key="cat" :value="cat">{{ cat }}</a-option>
            </a-select>
            <a-input-search v-model="searchText" placeholder="搜索文章标题" @search="handleSearch" @keyup.enter="handleSearch"
              allow-clear style="width: 240px" />
          </div>
          <a-table :columns="columns" :data="articles" :loading="loading" :pagination="pagination" :row-selection="{
            type: 'checkbox',
            showCheckedAll: true,
            width: 50,
            fixed: true,
            checkStrictly: true,
            onlyCurrent: false
          }" row-key="id" @page-change="handlePageChange" @page-size-change="handlePageSizeChange" v-model:selectedKeys="selectedRowKeys">
            <template #status="{ record }">
              <a-tag :color="statusColorMap[record.status]">
                {{ statusTextMap[record.status] }}
              </a-tag>
            </template>
            <template #actions="{ record }">
              <a-space>
                <a-button type="text" @click="viewArticle(record)" :title="record.id">
                  <template #icon><icon-eye /></template>
                </a-button>
                <a-button type="text" status="danger" @click="deleteArticle(record.id)">
                  <template #icon><icon-delete /></template>
                </a-button>
              </a-space>
            </template>
          </a-table>


          <a-modal v-model:visible="refreshModalVisible" title="刷新设置">
            <a-form :model="refreshForm" :rules="refreshRules">
              <a-form-item label="起始页" field="startPage">
                <a-input-number v-model="refreshForm.startPage" :min="1" />
              </a-form-item>
              <a-form-item label="结束页" field="endPage">
                <a-input-number v-model="refreshForm.endPage" :min="1" />
              </a-form-item>
            </a-form>
            <template #footer>
              <a-button @click="refreshModalVisible = false">取消</a-button>
              <a-button type="primary" @click="handleRefresh">确定</a-button>
            </template>
          </a-modal>

          <!-- AI 配置弹窗 -->
          <a-modal v-model:visible="aiConfigVisible" title="AI 分析配置" @ok="handleSaveAiConfig">
            <a-form :model="aiConfigForm" layout="vertical">
              <a-form-item label="AI API Key" help="设置 AI API 密钥">
                <a-input-password v-model="aiConfigForm.AI_API_KEY" placeholder="sk-..." />
              </a-form-item>
              <a-form-item label="API URL" help="AI 接口地址">
                <a-input v-model="aiConfigForm.AI_API_URL" placeholder="https://api.minimax.chat/v1/text/chatcompletion_v2" />
              </a-form-item>
              <a-form-item label="模型名称" help="使用的模型 ID">
                <a-input v-model="aiConfigForm.AI_MODEL" placeholder="abab6.5-chat" />
              </a-form-item>
              <a-form-item label="Group ID" help="Minimax 账户的 Group ID (V2接口必备)">
                <a-input v-model="aiConfigForm.AI_GROUP_ID" placeholder="请输入 Group ID" />
              </a-form-item>
              <a-form-item label="Temperature" help="采样温度 (0.1 ~ 1.0)">
                <a-input-number v-model="aiConfigForm.AI_TEMPERATURE" :min="0.1" :max="1.0" :step="0.1" />
              </a-form-item>
            </a-form>
          </a-modal>

          <a-modal id="article-model" v-model:visible="articleModalVisible" 
            placement="left" :footer="false" :fullscreen="false" @before-close="resetScrollPosition">
            <h2 id="topreader">{{ currentArticle.title }}</h2>
            <div style="margin-top: 20px; color: var(--color-text-3); text-align: left">
              <a-link :href="currentArticle.url" target="_blank">查看原文</a-link>
              更新时间 ：{{ currentArticle.time }}
            <a-link @click="viewArticle(currentArticle,-1)" target="_blank">上一篇 </a-link>
            <a-space/>
            <a-link @click="viewArticle(currentArticle,1)" target="_blank">下一篇 </a-link>
            </div>
            <div ref="shadowContainer" style="width: 100%; height: auto;"></div>

            <div style="margin-top: 20px; color: var(--color-text-3); text-align: right">
              {{ currentArticle.time }}
            </div>
          </a-modal>
        </a-card>
      </a-layout-content>
    </a-layout>
  </a-spin>
</template>

<script setup lang="ts">
import { ref, onMounted, h, nextTick, watch, computed, inject } from 'vue'
import { Avatar } from '@/utils/constants'
import { translatePage, setCurrentLanguage } from '@/utils/translate';
import http from '@/api/http'
import { IconApps, IconAt, IconDelete, IconEdit, IconEye, IconRefresh, IconScan, IconWeiboCircleFill, IconWifi, IconCode, IconCheck, IconClose, IconStop, IconPlayArrow, IconCopy, IconPlus, IconDown, IconExport, IconImport, IconShareExternal, IconThunderbolt } from '@arco-design/web-vue/es/icon'
import { Tag as ATag } from '@arco-design/web-vue'
import { getArticles, deleteArticle as deleteArticleApi, ClearArticle, ClearDuplicateArticle, getArticleDetail, toggleArticleReadStatus, analyzeArticle } from '@/api/article'
import { ExportOPML, ExportMPS, ImportMPS } from '@/api/export'
import { Message, Modal } from '@arco-design/web-vue'
import ExportModal from '@/components/ExportModal.vue'
import { getSubscriptions, UpdateMps, toggleMpStatus as toggleMpStatusApi, deleteMpApi } from '@/api/subscription'
import { formatDateTime, formatTimestamp } from '@/utils/date'
import router from '@/router'
import TextIcon from '@/components/TextIcon.vue'
import { ProxyImage } from '@/utils/constants'

const aiConfigVisible = ref(false)
const aiConfigForm = ref({
  AI_API_KEY: '',
  AI_API_URL: '',
  AI_MODEL: '',
  AI_TEMPERATURE: 0.1,
  AI_GROUP_ID: ''
})

const showAiConfig = async () => {
  try {
    const res = await http.get('/wx/configs')
    const configs = (res as any).list || []
    configs.forEach((item: any) => {
      if (aiConfigForm.value.hasOwnProperty(item.config_key)) {
        (aiConfigForm.value as any)[item.config_key] = item.config_value
      }
    })
    aiConfigVisible.value = true
  } catch (err) {
    Message.error('获取配置失败')
  }
}

const handleSaveAiConfig = async () => {
  try {
    for (const key in aiConfigForm.value) {
      await http.post('/wx/configs', {
        config_key: key,
        config_value: (aiConfigForm.value as any)[key].toString()
      })
    }
    Message.success('配置已保存')
    aiConfigVisible.value = false
  } catch (err) {
    Message.error('保存配置失败')
  }
}

const articles = ref([])
const loading = ref(false)
const mpList = ref([])
const mpLoading = ref(false)
const activeMpId = ref('')
const exportModal = ref()
const selectedRowKeys = ref([])
const mpPagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showPageSize: false,
  showJumper: false,
  showTotal: true,
  pageSizeOptions: [5, 10, 15]
})
const mpFilterType = ref('active') // 'active' | 'disabled' | 'all'
const searchText = ref('')
const filterStatus = ref('')
const mpSearchText = ref('')
const dateRange = ref([])
const aiCategory = ref('')

// AI 分析相关
const analyzeModalVisible = ref(false)
const analyzing = ref(false)
const analyzePercent = ref(0)
const analyzeProgressText = ref('')
const analyzeLogs = ref([])
const analyzeStatus = ref<'normal' | 'success' | 'warning' | 'danger'>('normal')
const logContainer = ref(null)

// AI 分类配置与颜色映射
const AI_CATEGORY_CONFIG: Record<string, { color: string }> = {
  '产品功能': { color: 'arcoblue' },
  '运营活动': { color: 'gold' },
  '其他': { color: 'gray' }
}

const addLog = (msg: string, type: 'info' | 'error' = 'info') => {
  const time = new Date().toLocaleTimeString()
  analyzeLogs.value.push({ time, msg, type })
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const handleBatchAnalyze = async () => {
  if (selectedRowKeys.value.length === 0 || analyzing.value) return

  console.log("DEBUG: handleBatchAnalyze V5-FIX triggered. Total:", selectedRowKeys.value.length)
  analyzeModalVisible.value = true
  analyzing.value = true
  analyzePercent.value = 0
  analyzeLogs.value = []
  analyzeStatus.value = 'normal'

  // 冻结当前选中的 ID，防止循环过程中被界面修改影响计算
  const taskIds = [...selectedRowKeys.value]
  let total = taskIds.length

  // 安全检查：确保 total 有效
  if (total <= 0) {
    analyzePercent.value = 100
    analyzing.value = false
    analyzeStatus.value = 'warning'
    analyzeProgressText.value = '没有可分析的文章'
    return
  }

  analyzeProgressText.value = `准备分析 ${total} 篇文章...`
  addLog(`开始批量分析任务，共 ${total} 篇文章`)

  let successCount = 0
  let failCount = 0

  try {
    for (let i = 0; i < total; i++) {
      // 检查分析任务是否因关闭弹窗而中断
      if (!analyzeModalVisible.value) {
        addLog("任务被用户中断", 'error')
        break
      }

      const articleId = taskIds[i]
      const article = articles.value.find(a => a.id === articleId)
      const title = article ? article.title : articleId

      analyzeProgressText.value = `正在分析 (${i + 1}/${total}): ${title}`
      addLog(`正在分析: ${title}...`)

      try {
        await analyzeArticle(articleId)
        successCount++
        addLog(`✅ 分析成功: ${title}`, 'info')
      } catch (err) {
        failCount++
        const errorMsg = err.response?.data?.message || err.message || '调用 API 失败'
        addLog(`❌ 分析失败: ${title} (${errorMsg})`, 'error')
      }
      
      // 严谨百分比计算：Arco Design a-progress 接收 0-100 的数值
      const rawPercent = ((i + 1) / total) * 100
      analyzePercent.value = Math.min(100, Math.max(0, Math.floor(rawPercent)))
    }
  } finally {
    analyzing.value = false
    // 确保进度条显示 100%
    analyzePercent.value = 100
    analyzeStatus.value = failCount > 0 ? 'warning' : 'success'
    analyzeProgressText.value = `分析结束！成功: ${successCount}, 失败: ${failCount}`
    addLog(`任务统计。成功: ${successCount}, 失败: ${failCount}`)
    
    // 任务结束后清空选择并刷新
    selectedRowKeys.value = []
    fetchArticles()
  }
}

const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: true,
  showJumper: true,
  showPageSize: true,
  pageSizeOptions: [10, 20, 50, 100]
})

const statusTextMap = {
  published: '已发布',
  draft: '草稿',
  deleted: '已删除'
}

const statusColorMap = {
  published: 'green',
  draft: 'orange',
  deleted: 'red'
}

// 已在上方定义

const columns = [
  {
    title: '已阅',
    dataIndex: 'is_read',
    width: '100',
    render: ({ record }) => {
      const isRead = record.is_read === 1;
      return h('div', { 
        style: { 
          display: 'flex', 
          alignItems: 'center', 
          cursor: 'pointer',
          color: isRead ? 'var(--color-success)' : 'var(--color-text-3)'
        },
        onClick: () => toggleReadStatus(record)
      }, [
        h(isRead ? IconCheck : IconClose, { 
          style: { marginRight: '4px' } 
        }),
        h('span', { 
          style: { fontSize: '12px' } 
        }, isRead ? '已读' : '未读')
      ]);
    }
  },
  {
    title: '文章标题',
    dataIndex: 'title',
    minWidth: 300,
    ellipsis: true,
    render: ({ record }) => h('div', { style: 'display:flex; align-items:center; gap:8px; overflow:hidden;' }, [
      record.ai_category ? h(ATag, {
        color: AI_CATEGORY_CONFIG[record.ai_category]?.color || 'gray',
        size: 'small',
        style: {
          cursor: 'help',
          flexShrink: 0
        },
        title: record.ai_summary || record.ai_category
      }, () => record.ai_category) : null,
      h('a', {
        href: issourceUrl.value ? record.url || '#' : "/views/article/" + record.id,
        title: record.title,
        target: '_blank',
        style: { 
          color: 'var(--color-text-1)',
          textDecoration: record.is_read === 1 ? 'line-through' : 'none',
          opacity: record.is_read === 1 ? 0.7 : 1,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }
      }, record.title)
    ])
  },
  {
    title: '公众号',
    dataIndex: 'mp_id',
    width: '120',
    ellipsis: true,
    render: ({ record }) => {
      const mp = mpList.value.find(item => item.id === record.mp_id);
      return h('a', {
        style: {
          color: 'var(--color-link)',
          cursor: 'pointer',
          textDecoration: 'none'
        },
        onClick: (e: MouseEvent) => {
          e.preventDefault()
          handleMpClick(record.mp_id)
        }
      }, record.mp_name || mp?.name || record.mp_id)
    }
  },
  {
    title: '更新时间',
    dataIndex: 'created_at',
    width: '140',
    render: ({ record }) => h('span',
      { style: { color: 'var(--color-text-3)', fontSize: '12px' } },
      formatDateTime(record.created_at)
    )
  },
  {
    title: 'AI分类理由',
    dataIndex: 'ai_reason',
    width: '200',
    ellipsis: true,
    tooltip: true,
    render: ({ record }) => h('span', { style: { fontSize: '12px', color: 'var(--color-text-2)' } }, record.ai_reason || '-')
  },
  {
    title: 'AI总结',
    dataIndex: 'ai_summary',
    width: '250',
    ellipsis: true,
    tooltip: true,
    render: ({ record }) => h('span', { style: { fontSize: '12px', color: 'var(--color-text-3)' } }, record.ai_summary || '-')
  },
  {
    title: '发布时间',
    dataIndex: 'publish_time',
    width: '140',
    render: ({ record }) => h('span',
      { style: { color: 'rgb(var(--color-text-3))', fontSize: '12px' } },
      formatTimestamp(record.publish_time)
    )
  },
  {
    title: '操作',
    dataIndex: 'actions',
    slotName: 'actions'
  }
]

const handleMpPageChange = (page: number, pageSize: number) => {
  mpPagination.value.current = page
  mpPagination.value.pageSize = pageSize
  fetchMpList()
}

const handleMpSearch = () => {
  mpPagination.value.current = 1
  fetchMpList()
}
const rssFormat = ref('atom')
const activeFeed = ref({
  id: "",
  name: "全部",
})
// 切换公众号状态
const toggleMpStatus = async (mpId: string, newStatus: number) => {
  try {
    await toggleMpStatusApi(mpId, newStatus);
    Message.success(newStatus === 0 ? '公众号已禁用' : '公众号已启用');
    // 更新本地数据
    const index = mpList.value.findIndex(item => item.id === mpId);
    if (index !== -1) {
      (mpList.value[index] as any).status = newStatus;
    }
  } catch (error) {
    console.error('更新公众号状态失败:', error);
    Message.error('更新公众号状态失败');
  }
}

const handleMpClick = (mpId: string) => {
  activeMpId.value = mpId
  pagination.value.current = 1
  activeFeed.value = mpList.value.find(item => item.id === activeMpId.value) || { id: "", name: "全部" }
  console.log(activeFeed.value)

  fetchArticles()
}

const fetchArticles = async () => {
  loading.value = true
  try {
    console.log('请求参数:', {
      page: pagination.value.current - 1,
      pageSize: pagination.value.pageSize,
      search: searchText.value,
      status: filterStatus.value,
      mp_id: activeMpId.value,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      ai_category: aiCategory.value || undefined
    })

    const res = (await getArticles({
      page: pagination.value.current - 1,
      pageSize: pagination.value.pageSize,
      search: searchText.value,
      status: filterStatus.value,
      mp_id: activeMpId.value,
      start_date: dateRange.value?.[0] || undefined,
      end_date: dateRange.value?.[1] || undefined,
      ai_category: aiCategory.value || undefined
    })) as any

    // 确保数据包含必要字段
    articles.value = (res.list || []).map((item: any) => ({
      ...item,
      mp_name: item.mp_name || item.account_name || '未知公众号',
      publish_time: item.publish_time || item.create_time || '-',
      url: item.url || "https://mp.weixin.qq.com/s/" + item.id
    }))
    pagination.value.total = res.total || 0
  } catch (error) {
    console.error('获取文章列表错误:', error)
    Message.error(error)
  } finally {
    loading.value = false
  }
}
const issourceUrl = ref(false)

// 过滤后的公众号列表
const filteredMpList = computed(() => {
  if (mpFilterType.value === 'all') {
    return mpList.value
  }
  if (mpFilterType.value === 'disabled') {
    return mpList.value.filter(item => item.status === 0)
  }
  // 'active' - 默认只显示启用的和"全部"选项
  return mpList.value.filter(item => item.status !== 0 || item.id === '')
})

// 从 localStorage 读取 issourceUrl 值
const initIssourceUrl = () => {
  const savedValue = localStorage.getItem('issourceUrl')
  if (savedValue !== null) {
    issourceUrl.value = savedValue === 'true'
  }
}

// 监听 issourceUrl 变化并保存到 localStorage
watch(issourceUrl, (newValue) => {
  localStorage.setItem('issourceUrl', newValue.toString())
}, { immediate: false })
const handlePageChange = (page: number) => {
  console.log('分页事件触发:', { page })
  pagination.value.current = page
  fetchArticles()
}

const handlePageSizeChange = (pageSize: number) => {
  console.log('页面大小改变:', { pageSize })
  pagination.value.pageSize = pageSize
  pagination.value.current = 1 // 切换页面大小时重置到第一页
  fetchArticles()
}

const handleSearch = () => {
  pagination.value.current = 1
  fetchArticles()
}

const wechatAuthQrcodeRef = ref()
const showAuthQrcode = inject('showAuthQrcode') as () => void
const handleAuthClick = () => {
  showAuthQrcode()
}

const exportOPML = async () => {
  try {
    const response = await ExportOPML();
    const blob = new Blob([response], { type: 'application/xml' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'rss_feed.opml';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('导出OPML失败:', error);
    Message.error(error?.message || '导出OPML失败');
  }
};
const exportMPS = async () => {
  try {
    const res = await ExportMPS();
    const data = (res as any).data ?? res;
    const blob = data instanceof Blob
      ? data
      : new Blob([data], { type: 'text/csv;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '公众号列表.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error: any) {
    Message.error(error?.message || '导出公众号失败');
  }
};

const importMPS = async () => {
  try {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = async (e: Event) => {
      const target = e.target as HTMLInputElement;
      const file = target.files?.[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      const response = await ImportMPS(formData) as any;
      Message.info(response?.message || "导入成功");
    };
    input.click();
  } catch (error) {
    Message.error(error?.message || '导入公众号失败');
  }
};

const openRssFeed = () => {
  const validFormats = ['rss', 'atom', 'json', 'md', 'txt'];
  const format = validFormats.includes(rssFormat.value)
    ? rssFormat.value
    : 'atom'
  let search = ""
  if (searchText.value != "") {
    search = "/search/" + searchText.value;
  }
  if (!activeMpId.value) {
    window.open(`/feed${search}/all.${format}`, '_blank')
    return
  }
  const activeMp = mpList.value.find(item => item.id === activeMpId.value)
  if (activeMp) {
    window.open(`/feed${search}/${activeMpId.value}.${format}`, '_blank')
  }
}

const resetScrollPosition = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}

const fullLoading = ref(false)

const refreshModalVisible = ref(false)
const refreshForm = ref({
  startPage: 0,
  endPage: 1
})
const refreshRules = {
  startPage: [{ required: true, message: '请输入开始页码' }],
  endPage: [{ required: true, message: '请输入结束页码' }]
}

const showRefreshModal = () => {
  refreshModalVisible.value = true
}

const handleRefresh = () => {
  fullLoading.value = true
  UpdateMps(activeMpId.value, {
    start_page: refreshForm.value.startPage,
    end_page: refreshForm.value.endPage
  }).then(() => {
    Message.success('刷新成功')
    refreshModalVisible.value = false
  }).finally(() => {
    fullLoading.value = false
  })
  fetchArticles()
}
const clear_articles = () => {
  fullLoading.value = true
  ClearArticle().then((res) => {
    Message.success(res?.message || '清理成功')
    refreshModalVisible.value = false
  }).finally(() => {
    fullLoading.value = false
  })
  fetchArticles()
}
const clear_duplicate_article = () => {
  fullLoading.value = true
  ClearDuplicateArticle().then((res) => {
    Message.success(res?.message || '清理成功')
    refreshModalVisible.value = false
  }).finally(() => {
    fullLoading.value = false
  })
  fetchArticles()
}

const processedContent = (record: any) => {
  return ProxyImage(record.content)
}

const viewArticle = async (record: any, action_type: number = 0) => {
  loading.value = true
  try {
    const article = (await getArticleDetail(record.id, action_type)) as any
    currentArticle.value = {
      id: article.id,
      title: article.title,
      content: processedContent(article),
      time: formatDateTime(article.created_at),
      url: article.url
    }
    articleModalVisible.value = true
    window.location.hash = "topreader"
    
    // 创建或更新 Shadow DOM
    await nextTick()
    createShadowHost()
    
    // 自动标记为已读（仅在从列表点击进入时）
    if (action_type === 0 && record.is_read !== 1) {
      await toggleReadStatus(record)
    }
  } catch (error) {
    console.error('获取文章详情错误:', error)
    Message.error(error as string)
  } finally {
    loading.value = false
  }
}

const refresh = () => {
  showRefreshModal()
}

const showAddModal = () => {
  router.push('/add-subscription')
}

const handleAddSuccess = () => {
  fetchArticles()
}
const currentArticle = ref({
  id: '',
  title: '',
  content: '',
  time: '',
  url: ''
})
const articleModalVisible = ref(false)
const shadowContainer = ref()

const deleteArticle = (id: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除该文章吗？删除后将无法恢复。',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      await deleteArticleApi(id);
      Message.success('删除成功');
      fetchArticles();
    },
    onCancel: () => {
      Message.info('已取消删除操作');
    }
  });
}

const handleBatchDelete = () => {
  Modal.confirm({
    title: '确认批量删除',
    content: `确定要删除选中的${selectedRowKeys.value.length}篇文章吗？删除后将无法恢复。`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await Promise.all(selectedRowKeys.value.map(id => deleteArticleApi(id)));
        Message.success(`成功删除${selectedRowKeys.value.length}篇文章`);
        selectedRowKeys.value = [];
        fetchArticles();
      } catch (error) {
        Message.error('删除部分文章失败');
      }
    },
    onCancel: () => {
      Message.info('已取消批量删除操作');
    }
  });
}

const handleExportShow = async () => {
  let mp_id=activeFeed.value?.id
  let ids=selectedRowKeys.value
  let mp_name=activeFeed.value?.name || activeFeed.value?.mp_name || '全部'
  exportModal.value.show(mp_id,ids,mp_name)
}


onMounted(() => {
  console.log('组件挂载，开始获取数据')
  initIssourceUrl() // 初始化 issourceUrl 值
  fetchMpList().then(() => {
    console.log('公众号列表获取完成')
    fetchArticles()
  }).catch(err => {
    console.error('初始化失败:', err)
  })
})

const fetchMpList = async () => {
  mpLoading.value = true
  try {
    const res = (await getSubscriptions({
      page: mpPagination.value.current - 1,
      pageSize: mpPagination.value.pageSize,
      kw: mpSearchText.value
    })) as any

    mpList.value = res.list.map(item => ({
      id: item.id || item.mp_id,
      name: item.name || item.mp_name,
      avatar: item.avatar || item.mp_cover || '',
      mp_intro: item.mp_intro || item.mp_intro || '',
      article_count: item.article_count || 0,
      status: item.status ?? 1
    }))
    // 添加'全部'选项 - 只在没有搜索时显示
    if (!mpSearchText.value) {
      mpList.value.unshift({
        id: '',
        name: '全部',
        avatar: '/static/logo.svg',
        mp_intro: '显示所有公众号文章',
        article_count: res.total || 0,
        status: 1
      });
    }
    mpPagination.value.total = res.total || 0
  } catch (error) {
    console.error('获取公众号列表错误:', error)
  } finally {
    mpLoading.value = false
  }
}

const copyMpId = async (mpId: string) => {
  try {
    await navigator.clipboard.writeText(mpId);
    Message.success('MP ID 已复制到剪贴板');
  } catch (error) {
    // 如果 clipboard API 不可用，使用传统方法
    const textArea = document.createElement('textarea');
    textArea.value = mpId;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      Message.success('MP ID 已复制到剪贴板');
    } catch (err) {
      Message.error('复制失败，请手动复制');
      console.error('复制失败:', err);
    }
    document.body.removeChild(textArea);
  }
}

const deleteMp = async (mpId: string) => {
  try {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除该订阅号吗？删除后将无法恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        await deleteMpApi(mpId);
        Message.success('订阅号删除成功');
        fetchMpList();
      },
      onCancel: () => {
        Message.info('已取消删除操作');
      }
    });
  } catch (error) {
    console.error('删除订阅号失败:', error);
    Message.error('删除订阅号失败，请稍后重试');
  }
}

// 公众号状态切换逻辑已在上方定义

const importArticles = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  input.onchange = async (e: Event) => {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;

    try {
      const content = await file.text();
      const data = JSON.parse(content);
      // 这里应该调用API导入数据
      Message.success(`成功导入${data.length}篇文章`);
    } catch (error) {
      console.error('导入文章失败:', error);
      Message.error('导入失败，请检查文件格式');
    }
  };
  input.click();
};

const exportArticles = () => {
  if (!articles.value.length) {
    Message.warning('没有文章可导出');
    return;
  }

  const data = JSON.stringify(articles.value, null, 2);
  const blob = new Blob([data], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `articles_${activeMpId.value || 'all'}_${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  Message.success('导出成功');
};

// 创建 Shadow DOM 隔离容器
const createShadowHost = () => {
  if (!shadowContainer.value) return;
  
  // 清空容器
  shadowContainer.value.innerHTML = '';
  
  // 创建 Shadow Host
  const shadowHost = document.createElement('div');
  shadowHost.style.width = '100%';
  shadowHost.style.height = 'auto';
  
  // 创建 Shadow Root
  const shadowRoot = shadowHost.attachShadow({ mode: 'open' });
  
  // 添加基础样式到 Shadow DOM
  const style = document.createElement('style');
  style.textContent = `
    :host {
      display: block;
      width: 100%;
      height: auto;
    }
    img {
      max-width: 100% !important;
      height: auto !important;
      display: block;
      margin: 0 auto;
    }
    iframe {
      width: 100% !important;
      border: none !important;
    }
    p {
      margin: 1em 0;
      line-height: 1.6;
    }
    * {
      box-sizing: border-box;
    }
  `;
  shadowRoot.appendChild(style);
  
  // 创建内容容器
  const contentDiv = document.createElement('div');
  contentDiv.innerHTML = currentArticle.value.content || '';
  shadowRoot.appendChild(contentDiv);
  
  // 将 Shadow Host 添加到容器中
  shadowContainer.value.appendChild(shadowHost);
};

// 切换文章阅读状态
const toggleReadStatus = async (record: any) => {
  try {
    const newReadStatus = record.is_read === 1 ? false : true;
    await toggleArticleReadStatus(record.id, newReadStatus);
    
    // 更新本地数据
    const index = articles.value.findIndex(item => item.id === record.id);
    if (index !== -1) {
      articles.value[index].is_read = newReadStatus ? 1 : 0;
    }
    
    Message.success(`文章已标记为${newReadStatus ? '已读' : '未读'}`);
  } catch (error) {
    console.error('更新阅读状态失败:', error);
    Message.error('更新阅读状态失败');
  }
};
</script>

<style scoped>
.article-list {
  /* height: calc(100vh - 186px); */
}

.a-layout-sider {
  overflow: hidden;
}

.a-list-item {
  cursor: pointer;
  padding: 12px 16px;
  transition: all 0.2s;
  margin-bottom: 0 !important;
}

.a-list-item:hover {
  background-color: var(--color-fill-2);
}

.active-mp {
  background-color: var(--color-primary-light-1);
}

.search-bar {
  display: flex;
  margin-bottom: 20px;
}

.arco-drawer-body img {
  max-width: 100vw !important;
  margin: 0 auto !important;
  padding: 0 !important;
}

.arco-drawer-body {
  z-index: 9999 !important;
  /* 确保抽屉在其他内容之上 */
}

:deep(.arco-btn .arco-icon-down) {
  transition: transform 0.2s ease-in-out;
}

:deep(.arco-dropdown-open .arco-icon-down) {
  transform: rotate(180deg);
}

</style>
<style>
#article-model img {
  max-width: 100% !important;
  border-width:0px !important;
}
iframe{
  width:100% !important;
  border:0 !important;
}
</style>