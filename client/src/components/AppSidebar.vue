<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed, 'mobile-open': isMobileOpen }">
    <div class="sidebar-brand">
      <span class="brand-mark">●</span>
      <span class="brand-text" v-show="!isCollapsed">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
      </span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :title="isCollapsed ? t(item.labelKey) : null"
        @click="closeMobile"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span class="nav-label" v-show="!isCollapsed">{{ t(item.labelKey) }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <div class="sidebar-footer-slot" v-show="!isCollapsed">
        <slot name="footer" />
      </div>
      <button
        class="collapse-toggle"
        @click="toggleCollapse"
        :aria-label="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        {{ isCollapsed ? '»' : '«' }}
      </button>
    </div>
  </aside>

  <div class="mobile-topbar">
    <button class="hamburger" @click="isMobileOpen = true" aria-label="Open navigation">
      <span></span><span></span><span></span>
    </button>
    <span class="mobile-page-title">{{ currentPageLabel }}</span>
  </div>
  <div v-if="isMobileOpen" class="mobile-backdrop" @click="closeMobile"></div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'

const ICONS = {
  overview: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2.5" y="2.5" width="6.5" height="6.5" rx="1.2"/><rect x="11" y="2.5" width="6.5" height="6.5" rx="1.2"/><rect x="2.5" y="11" width="6.5" height="6.5" rx="1.2"/><rect x="11" y="11" width="6.5" height="6.5" rx="1.2"/></svg>',
  inventory: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2.5 6.5 10 2.5l7.5 4v7L10 17.5 2.5 13.5z"/><path d="M2.5 6.5 10 10.5l7.5-4"/><path d="M10 10.5v7"/></svg>',
  orders: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4" y="3.5" width="12" height="14" rx="1.5"/><path d="M7.5 2.5h5v2h-5z"/><path d="M6.5 9h7M6.5 12h7M6.5 15h4.5"/></svg>',
  demand: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2.5 15 8 9.5l3 3 6.5-7"/><path d="M13.5 5.5h4v4"/></svg>',
  restocking: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 5h2l1.2 8.2A1.5 1.5 0 0 0 7.7 14.5H15a1.5 1.5 0 0 0 1.5-1.2L17.5 7H6"/><circle cx="8" cy="17" r="1.1" fill="currentColor" stroke="none"/><circle cx="15" cy="17" r="1.1" fill="currentColor" stroke="none"/></svg>',
  finance: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3.5 16.5v-6M8.5 16.5V6M13.5 16.5v-9M17.5 16.5V3.5"/></svg>',
  reports: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5.5 2.5h6l3 3v12h-9z"/><path d="M11.5 2.5v3h3"/><path d="M7.5 10.5h5M7.5 13.5h5"/></svg>'
}

export default {
  name: 'AppSidebar',
  setup() {
    const { t } = useI18n()
    const route = useRoute()

    const isCollapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
    const isMobileOpen = ref(false)

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
      localStorage.setItem('sidebar-collapsed', String(isCollapsed.value))
    }

    const closeMobile = () => {
      isMobileOpen.value = false
    }

    const navItems = [
      { path: '/', labelKey: 'nav.overview', icon: ICONS.overview },
      { path: '/inventory', labelKey: 'nav.inventory', icon: ICONS.inventory },
      { path: '/orders', labelKey: 'nav.orders', icon: ICONS.orders },
      { path: '/demand', labelKey: 'nav.demandForecast', icon: ICONS.demand },
      { path: '/restocking', labelKey: 'nav.restocking', icon: ICONS.restocking },
      { path: '/spending', labelKey: 'nav.finance', icon: ICONS.finance },
      { path: '/reports', labelKey: 'nav.reports', icon: ICONS.reports }
    ]

    const currentPageLabel = computed(() => {
      const match = navItems.find(item => item.path === route.path)
      return match ? t(match.labelKey) : t('nav.companyName')
    })

    return {
      t,
      isCollapsed,
      isMobileOpen,
      toggleCollapse,
      closeMobile,
      navItems,
      currentPageLabel
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width-expanded);
  height: 100vh;
  position: sticky;
  top: 0;
  flex: none;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-surface);
  border-right: 1px solid var(--color-border-subtle);
  transition: width 0.2s ease;
  z-index: 100;
}

.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
  overflow: hidden;
}

.brand-mark {
  flex: none;
  color: var(--color-accent);
  font-size: 1.25rem;
  line-height: 1;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.025em;
  white-space: nowrap;
}

.brand-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  border-left: 3px solid transparent;
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: 500;
  white-space: nowrap;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: var(--color-bg-surface-hover);
  color: var(--color-text-primary);
}

.nav-item:focus-visible {
  box-shadow: var(--shadow-focus-ring);
  outline: none;
}

.nav-item.router-link-active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  border-left-color: var(--color-accent);
}

.nav-icon {
  flex: none;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

.sidebar-footer {
  border-top: 1px solid var(--color-border-subtle);
  padding: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.sidebar-footer-slot {
  flex: 1;
  min-width: 0;
}

.collapse-toggle {
  flex: none;
  width: 28px;
  height: 28px;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-sm);
  background: var(--color-bg-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: background 0.15s ease;
}

.collapse-toggle:hover {
  background: var(--color-bg-surface-hover);
}

.collapse-toggle:focus-visible {
  box-shadow: var(--shadow-focus-ring);
  outline: none;
}

.mobile-topbar {
  display: none;
}

.mobile-backdrop {
  display: none;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 200;
    width: var(--sidebar-width-expanded);
    transform: translateX(-100%);
    transition: transform 0.2s ease;
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .mobile-topbar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    height: 56px;
    padding: 0 var(--space-4);
    background: var(--color-bg-surface);
    border-bottom: 1px solid var(--color-border-subtle);
    position: sticky;
    top: 0;
    z-index: 90;
  }

  .hamburger {
    flex: none;
    width: 32px;
    height: 32px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    background: none;
    border: none;
    cursor: pointer;
  }

  .hamburger span {
    display: block;
    width: 18px;
    height: 2px;
    background: var(--color-text-primary);
    border-radius: 1px;
  }

  .mobile-page-title {
    font-weight: 600;
    font-size: var(--font-size-base);
    color: var(--color-text-primary);
  }

  .mobile-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: 150;
  }
}
</style>
