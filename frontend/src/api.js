const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
    ...options,
  })
  if (!response.ok) {
    throw new Error('Не удалось получить данные от сервера.')
  }
  return response.json()
}

export const getDashboard = () => request('/api/dashboard')

export const calculatePlan = (payload) => request('/api/plans/calculate', {
  method: 'POST',
  body: JSON.stringify(payload),
})

export const approvePlan = (plan_number) => request('/api/plans/approve', {
  method: 'POST',
  body: JSON.stringify({ plan_number }),
})
