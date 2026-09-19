import { useEffect, useState } from 'react'
import { approvePlan, calculatePlan, getDashboard } from './api'

const navigation = [
  { id: 'dashboard', icon: '▦', label: 'Обзор' },
  { id: 'plans', icon: '▣', label: 'Производственные планы' },
  { id: 'orders', icon: '▤', label: 'Заказы' },
  { id: 'inventory', icon: '▧', label: 'Запасы и партии' },
  { id: 'tasks', icon: '▥', label: 'Производственные задания' },
  { id: 'reports', icon: '◔', label: 'Отчёты' },
]

function StatusPill({ kind = 'info', children }) {
  return <span className={`pill pill--${kind}`}>{children}</span>
}

function MetricCard({ metric }) {
  return (
    <article className="metric-card">
      <p>{metric.label}</p>
      <div className="metric-card__value">
        <strong>{metric.value}</strong>
        <StatusPill kind={metric.kind}>{metric.detail}</StatusPill>
      </div>
    </article>
  )
}

function Sidebar({ activeView, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand__symbol">+</span>
        <div>
          <strong>FEFO‑План</strong>
          <small>ПРОИЗВОДСТВО</small>
        </div>
      </div>
      <p className="sidebar__caption">РАБОЧЕЕ ПРОСТРАНСТВО</p>
      <nav className="sidebar__nav" aria-label="Основная навигация">
        {navigation.map((item) => (
          <button
            className={activeView === item.id ? 'nav-item nav-item--active' : 'nav-item'}
            key={item.id}
            onClick={() => onNavigate(item.id)}
          >
            <span aria-hidden="true">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>
      <div className="sidebar__footer">
        <button className="nav-item"><span aria-hidden="true">⚙</span>Настройки</button>
        <div className="user-card">
          <span className="avatar">АЛ</span>
          <div><strong>Александр Лейкин</strong><small>Планировщик производства</small></div>
        </div>
      </div>
    </aside>
  )
}

function Topbar({ title, breadcrumb, onCreate }) {
  return (
    <header className="topbar">
      <div>
        <p className="breadcrumbs">{breadcrumb}</p>
        <h1>{title}</h1>
      </div>
      <div className="topbar__actions">
        <span className="date-chip">▣&nbsp; Сегодня, 19.09</span>
        {onCreate && <button className="button button--primary" onClick={onCreate}>+ Создать план</button>}
      </div>
    </header>
  )
}

function Dashboard({ data, onCreate }) {
  if (!data) return <div className="loading-panel">Загрузка рабочего стола…</div>

  return (
    <>
      <Topbar title="Рабочий стол" breadcrumb="Главная  /  Обзор" onCreate={onCreate} />
      <p className="page-intro">Оперативная сводка по производству на {data.date_label}</p>
      <section className="metrics-grid" aria-label="Ключевые показатели">
        {data.metrics.map((metric) => <MetricCard metric={metric} key={metric.label} />)}
      </section>
      <section className="content-card orders-card">
        <div className="section-heading">
          <div><h2>Приоритетные заказы</h2><p>Заказы с ближайшим сроком отгрузки и текущим статусом планирования.</p></div>
          <button className="link-button">Все заказы →</button>
        </div>
        <div className="table-scroll">
          <table>
            <thead><tr><th>Заказ</th><th>Продукция</th><th>Объём</th><th>Отгрузка</th><th>Статус</th></tr></thead>
            <tbody>
              {data.orders.map((order) => (
                <tr key={order.number}>
                  <td>{order.number}</td><td>{order.product}</td><td>{order.quantity}</td><td>{order.delivery_date}</td>
                  <td><StatusPill kind={order.status_kind}>{order.status}</StatusPill></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="table-note">Показаны 3 из 12 заказов</p>
      </section>
      <section className="risk-banner">
        <span className="risk-banner__icon">!</span>
        <div><h3>3 партии требуют использования в течение 48 часов</h3><p>Проверьте рекомендации алгоритма FEFO перед формированием плана.</p></div>
        <button className="link-button">Открыть →</button>
      </section>
    </>
  )
}

function PlanBuilder({ onBack, notify }) {
  const [form, setForm] = useState({ period_start: '2026-09-19', period_end: '2026-09-20', production_line: 'all', order_count: 12 })
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const updateField = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))

  async function handleCalculate(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await calculatePlan({ ...form, order_count: Number(form.order_count) })
      setPlan(result)
      notify('Проект FEFO‑плана сформирован.')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleApprove() {
    try {
      const result = await approvePlan(plan.plan_number)
      notify(result.message)
      setPlan((current) => ({ ...current, approved: true }))
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  return (
    <>
      <Topbar title="Новый производственный план" breadcrumb="Производственные планы  /  Новый план" />
      <div className="stepper" aria-label="Ход формирования плана">
        <span className="stepper__item stepper__item--active"><b>1</b> Параметры расчёта</span>
        <span className={plan ? 'stepper__item stepper__item--active' : 'stepper__item'}><b>2</b> Проверка и утверждение</span>
      </div>
      <div className="builder-grid">
        <form className="content-card plan-form" onSubmit={handleCalculate}>
          <div className="section-heading"><div><h2>Параметры расчёта</h2><p>Задайте период, линию и состав заказов для формирования плана.</p></div></div>
          <label>Период планирования<div className="date-range"><input type="date" name="period_start" value={form.period_start} onChange={updateField} required /><span>—</span><input type="date" name="period_end" value={form.period_end} onChange={updateField} min={form.period_start} required /></div></label>
          <label>Производственная линия<select name="production_line" value={form.production_line} onChange={updateField}><option value="all">Все доступные линии</option><option value="line-1">Линия № 1</option><option value="line-2">Линия № 2</option></select></label>
          <label>Заказы для включения в план<select name="order_count" value={form.order_count} onChange={updateField}><option value="12">12 выбранных заказов</option><option value="8">8 выбранных заказов</option><option value="5">5 выбранных заказов</option></select></label>
          <button className="button button--primary button--wide" disabled={loading}>{loading ? 'Выполняется расчёт…' : 'Запустить расчёт FEFO'}</button>
          {error && <p className="form-error">{error}</p>}
        </form>
        <aside className="info-card"><span className="info-card__number">01</span><h3>Что произойдёт после запуска</h3><p>Система подберёт партии с ближайшим сроком годности, проверит доступные объёмы и сформирует проект производственного плана.</p><ul><li>Учитывается срок годности партии.</li><li>Фиксируется адрес хранения.</li><li>Отображаются критичные партии.</li></ul></aside>
      </div>
      {plan && <section className="content-card result-card">
        <div className="section-heading"><div><span className="eyebrow">{plan.plan_number}</span><h2>Рекомендации алгоритма FEFO</h2><p>{plan.message}</p></div><div className="result-summary"><span>{plan.summary.tasks} задания</span><span>{plan.summary.critical_batches} критичная партия</span><span>{plan.summary.conflicts} конфликтов</span></div></div>
        <div className="table-scroll"><table><thead><tr><th>Продукция</th><th>Плановый объём</th><th>Партия</th><th>Ячейка</th><th>Срок годности</th><th>Приоритет</th></tr></thead><tbody>{plan.recommendations.map((item) => <tr key={item.product}><td>{item.product}</td><td>{item.volume}</td><td>{item.batch}</td><td>{item.location}</td><td>{item.expiry}</td><td><StatusPill kind={item.priority_kind}>{item.priority}</StatusPill></td></tr>)}</tbody></table></div>
        <div className="approval-row"><p>Перед утверждением убедитесь, что критичные партии могут быть использованы в указанном порядке.</p><button className="button button--primary" onClick={handleApprove} disabled={plan.approved}>{plan.approved ? 'План утверждён' : 'Утвердить план'}</button></div>
      </section>}
      <button className="back-link" onClick={onBack}>← Вернуться к рабочему столу</button>
    </>
  )
}

function Placeholder({ view, onBack }) {
  const item = navigation.find((navigationItem) => navigationItem.id === view)
  return <section className="empty-state"><span>{item?.icon}</span><h1>{item?.label}</h1><p>Раздел предусмотрен в архитектуре интерфейса и будет реализован на следующем этапе разработки.</p><button className="button button--primary" onClick={onBack}>К рабочему столу</button></section>
}

function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [dashboard, setDashboard] = useState(null)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  useEffect(() => {
    getDashboard().then(setDashboard).catch((requestError) => setError(requestError.message))
  }, [])

  function notify(message) {
    setToast(message)
    window.setTimeout(() => setToast(''), 4000)
  }

  const content = activeView === 'dashboard'
    ? <Dashboard data={dashboard} onCreate={() => setActiveView('plans')} />
    : activeView === 'plans'
      ? <PlanBuilder onBack={() => setActiveView('dashboard')} notify={notify} />
      : <Placeholder view={activeView} onBack={() => setActiveView('dashboard')} />

  return (
    <div className="app-shell">
      <Sidebar activeView={activeView} onNavigate={setActiveView} />
      <main className="main-content">{error ? <div className="error-state">{error}</div> : content}</main>
      {toast && <div className="toast">✓ {toast}</div>}
    </div>
  )
}

export default App
