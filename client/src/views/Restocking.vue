<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-row">
        <label for="budget-slider" class="budget-label">{{ t('restocking.budgetLabel') }}</label>
        <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
      </div>
      <input
        id="budget-slider"
        type="range"
        class="budget-slider"
        min="0"
        :max="maxBudget"
        step="250"
        v-model.number="budget"
        @input="onBudgetChange"
      />
      <div class="budget-scale">
        <span>{{ currencySymbol }}0</span>
        <span>{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
      </div>
    </div>

    <div v-if="submittedOrder" class="success-banner">
      <div class="success-icon">✓</div>
      <div class="success-body">
        <div class="success-title">{{ t('restocking.successTitle') }}</div>
        <div class="success-message">
          {{ t('restocking.successMessage', {
            id: submittedOrder.id,
            count: submittedOrder.items.length,
            days: submittedOrder.lead_time_days
          }) }}
        </div>
      </div>
      <button class="btn-secondary" @click="goToOrders">{{ t('restocking.viewInOrders') }}</button>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.budget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ recommendations.budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.recommendedCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ recommendations.total_cost.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ recommendations.remaining_budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.itemCount') }}</div>
          <div class="stat-value">{{ recommendations.items.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.title') }}</h3>
          <button
            class="btn-primary"
            :disabled="recommendations.items.length === 0 || placing"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="recommendations.items.length === 0" class="no-data">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.stock') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations.items" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td>{{ translateWarehouse(item.warehouse) }}</td>
                <td>
                  <span :class="['badge', item.quantity_on_hand < item.reorder_point ? 'danger' : 'success']">
                    {{ item.quantity_on_hand }} / {{ item.reorder_point }}
                  </span>
                </td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td>{{ item.recommended_quantity }}</td>
                <td><strong>{{ currencySymbol }}{{ item.line_total.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

const DEBOUNCE_MS = 400

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()
    const router = useRouter()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const maxBudget = 50000
    const budget = ref(10000)
    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const submittedOrder = ref(null)
    const recommendations = ref({ budget: 0, total_cost: 0, remaining_budget: 0, items: [] })

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        recommendations.value = await api.getRestockingRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const onBudgetChange = () => {
      submittedOrder.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, DEBOUNCE_MS)
    }

    const placeOrder = async () => {
      if (recommendations.value.items.length === 0) return

      try {
        placing.value = true
        error.value = null
        const payload = {
          budget: budget.value,
          items: recommendations.value.items.map(item => ({
            sku: item.sku,
            name: item.name,
            category: item.category,
            quantity: item.recommended_quantity,
            unit_cost: item.unit_cost
          }))
        }
        submittedOrder.value = await api.createRestockingOrder(payload)
      } catch (err) {
        error.value = 'Failed to submit restocking order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    const goToOrders = () => {
      router.push('/orders')
    }

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    onMounted(loadRecommendations)

    return {
      t,
      budget,
      maxBudget,
      loading,
      error,
      placing,
      submittedOrder,
      recommendations,
      currencySymbol,
      onBudgetChange,
      placeOrder,
      goToOrders,
      translateCategory,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
}

.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: var(--color-border-subtle);
  appearance: none;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  border: none;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.btn-primary {
  background: var(--color-accent);
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.btn-primary:disabled {
  background: var(--color-border-default);
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: var(--color-success);
  border: 1px solid var(--color-border-subtle);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: var(--font-size-sm);
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s ease;
}

.btn-secondary:hover {
  background: var(--color-success-subtle);
}

.success-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--color-success-subtle);
  border: 1px solid #bbf7d0;
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
}

.success-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #16a34a;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.success-body {
  flex: 1;
}

.success-title {
  font-weight: 700;
  color: var(--color-success);
  font-size: var(--font-size-base);
}

.success-message {
  font-size: var(--font-size-sm);
  color: var(--color-success);
  margin-top: 0.125rem;
}

.no-data {
  padding: 2.5rem 1rem;
  text-align: center;
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
}

.badge.success {
  background: var(--color-success-subtle);
  color: var(--color-success);
}
</style>
