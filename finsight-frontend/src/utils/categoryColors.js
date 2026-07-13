// utils/categoryColors.js
// ─────────────────────────────────────────────────────────────────
// SINGLE SOURCE OF TRUTH for category colors.
// Import this everywhere — donut chart, bars, transaction icons,
// insight cards — so colors are always consistent.
//
// If you want to change a color, change it HERE ONLY.
// ─────────────────────────────────────────────────────────────────

export const CATEGORY_COLORS = {
  'Food & dining':      '#2563EB',
  'Housing':            '#7C3AED',
  'Transport':          '#0D9373',
  'Entertainment':      '#D97706',
  'Health':             '#E11D48',
  'Shopping':           '#0891B2',
  'Bills & utilities':  '#7C3AED',
  'Banking & transfers':'#64748B',
  'Income':             '#0D9373',
  'Others':             '#94A3B8',
}

// Light background version for icon containers
export const CATEGORY_BG = {
  'Food & dining':      '#DBEAFE',
  'Housing':            '#EDE9FE',
  'Transport':          '#D1FAE5',
  'Entertainment':      '#FEF3C7',
  'Health':             '#FFE4E6',
  'Shopping':           '#E0F2FE',
  'Bills & utilities':  '#EDE9FE',
  'Banking & transfers':'#F1F5F9',
  'Income':             '#D1FAE5',
  'Others':             '#F1F5F9',
}

// Tabler icon names per category
export const CATEGORY_ICONS = {
  'Food & dining':      'tools-kitchen-2',
  'Housing':            'home',
  'Transport':          'bus',
  'Entertainment':      'device-tv',
  'Health':             'heart-rate-monitor',
  'Shopping':           'shopping-bag',
  'Bills & utilities':  'bolt',
  'Banking & transfers':'building-bank',
  'Income':             'trending-up',
  'Others':             'dots-circle-horizontal',
}

// Helper: get color for a category (fallback to gray)
export const getColor = (category) =>
  CATEGORY_COLORS[category] ?? '#94A3B8'

// Helper: get background color for a category
export const getBg = (category) =>
  CATEGORY_BG[category] ?? '#F1F5F9'

// Helper: get icon for a category
export const getIcon = (category) =>
  CATEGORY_ICONS[category] ?? 'dots-circle-horizontal'
